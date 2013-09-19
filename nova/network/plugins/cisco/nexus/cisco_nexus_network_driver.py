# Copyright 2011 Cisco Systems, Inc.  All rights reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#
#    Debojyoti Dutta, Cisco Systems, Inc.
#    Edgar Magana, Cisco Systems Inc.
#    ONOP psvm@onop.org


"""
Implements a Nexus-OS NETCONF over SSHv2 API Client

:class: `CiscoNEXUSDriver` provides interface to Cisco NEXUS switch
by using the ncclient NETCONF library
"""

from ncclient import manager
import ncclient.transport.errors as ncce

from nova.network.plugins.cisco.common import cisco_exceptions as cexc
from nova.network.plugins.cisco.common import utils
from nova.network.plugins.cisco.nexus import cisco_nexus_snippets as snipp
from nova.openstack.common.gettextutils import _
from nova.openstack.common import log as logging

import random
import time


LOG = logging.getLogger(__name__)


class CiscoNEXUSDriver(object):
    """Nexus Driver Main Class."""
    def __init__(self, **kwargs):
        self.nexus_host = kwargs['host']
        self.username = kwargs['username']
        self.password = kwargs['password']

    def __enter__(self):
        try:
            self.mgr = self.nxos_connect()
        except cexc.NexusConnectFailed as e:
            LOG.exception(_("Failed to connect to nexus switch %(host)s with "
                            "username %(username)s, e: %(e)s"),
                          {'host': self.nexus_host, 'username': self.username,
                           'e': e})
            return None
        except Exception:
            raise
        LOG.debug(_("NEXUS Driver connected to switch %s"), self.nexus_host)
        return self

    def __exit__(self, type, value, traceback):
        if hasattr(self, 'mgr'):
            self.mgr.close_session()
            LOG.debug(_("NEXUS Driver disconnected from switch %s"),
                      self.nexus_host)

    def _edit_config(self, target='running', config='',
                     allowed_exc_strs=None):
        """Modify switch config for a target config type.

        :param target: Target config type
        :param config: Configuration string in XML format
        :param allowed_exc_strs: Exceptions which have any of these strings
                                 as a subset of their exception message
                                 (str(exception)) can be ignored

        :raises: NexusConfigFailed

        """
        if not allowed_exc_strs:
            allowed_exc_strs = []
        try:
            self.mgr.edit_config(target=target, config=config)
        except Exception as e:
            for exc_str in allowed_exc_strs:
                if exc_str in str(e):
                    LOG.debug("EXC_str %s matched E %s" % (exc_str, str(e)))
                    break
                else:
                    LOG.debug("no match: EXC_str %s E %s" % (exc_str, str(e)))
                    # Raise a Nexus exception. Include a description of
                    # the original ncclient exception. No need to preserve T/B
                    raise cexc.NexusConfigFailed(config=config, exc=e)

    def _get_config(self, xml_show_filter):
        """Send XML snippet containing the desired operational
           or running config output.

        :param xml_show_filter: XML show command snippet
        :raises: NexusConfigFailed
        :returns XML response from switch

        """
        try:
            return self.mgr.get(("subtree", xml_show_filter))
        except Exception as e:
            raise cexc.NexusConfigFailed(config=xml_show_filter, exc=e)

    def nxos_connect(self, retries=0):
        """Make SSH connection to the Nexus Switch."""

        try:
            try:
                return manager.connect(host=self.nexus_host,
                                       port=22,
                                       username=self.username,
                                       password=self.password,
                                       device_params={"name": "nexus"})
            except TypeError:
                return manager.connect(host=self.nexus_host,
                                       port=22,
                                       username=self.username,
                                       password=self.password)
        except ncce.SessionCloseError as sce:
            if retries > 7:
                LOG.debug("Retries to connect to NEXUS exceeded")
                raise
            if 'xml session exceeded max allowed' in str(sce):
                retries = retries + 1
                LOG.debug("Retrying connection to NEXUS, attempt %s" % retries)
                sleep_int = random.random() + .37
                time.sleep(sleep_int)
                return self.nxos_connect(retries)
            else:
                raise
        except Exception as e:
            # Raise a Neutron exception. Include a description of
            # the original ncclient exception.  No need to preserve T/B.
            LOG.exception(_("NEXUS DRIVER NXOS_CONNECT Failed to connect, %s"),
                          e)
            raise cexc.NexusConnectFailed(nexus_host=self.nexus_host, exc=e)

    def create_xml_snippet(self, cutomized_config):
        """Create XML snippet.

        Creates the Proper XML structure for the Nexus Switch Configuration.
        """
        conf_xml_snippet = snipp.EXEC_CONF_SNIPPET % (cutomized_config)
        return conf_xml_snippet

    def create_vlan(self, vlanid):
        """Create a VLAN on Nexus Switch given the VLAN ID and Name."""
        confstr = self.create_xml_snippet(
            snipp.CMD_VLAN_CONF_SNIPPET % vlanid)
        self._edit_config(target='running', config=confstr)

        # Enable VLAN active and no-shutdown states. Some versions of
        # Nexus switch do not allow state changes for the extended VLAN
        # range (1006-4094), but these errors can be ignored (default
        # values are appropriate).
        state_config = [snipp.CMD_VLAN_ACTIVE_SNIPPET,
                        snipp.CMD_VLAN_NO_SHUTDOWN_SNIPPET]
        for snippet in state_config:
            try:
                confstr = self.create_xml_snippet(snippet % vlanid)
                self._edit_config(
                    target='running',
                    config=confstr,
                    allowed_exc_strs=["Can't modify state for extended",
                                      "Command is only allowed on VLAN",
                                      "VLAN with the same name exists"])
            except cexc.NexusConfigFailed:
                LOG.exception(_("Failed to create VLAN %(vlanid)s on nexus "
                                "switch %(host)s"), {'vlanid': vlanid,
                                                     'host': self.nexus_host})

    def delete_vlan(self, vlanid):
        """Delete a VLAN on Nexus Switch given the VLAN ID."""
        confstr = snipp.CMD_NO_VLAN_CONF_SNIPPET % vlanid
        confstr = self.create_xml_snippet(confstr)
        self._edit_config(target='running', config=confstr)

    def enable_vlan_on_trunk_int(self, vlanid, etype, interface):
        """Enable a VLAN on a trunk interface."""
        xml_etype = utils.get_xml_etype(etype)
        snippet = snipp.CMD_INT_VLAN_ADD_SNIPPET
        confstr = snippet % (etype, interface, xml_etype, vlanid, xml_etype,
                             etype)
        confstr = self.create_xml_snippet(confstr)
        LOG.debug(_("NexusDriver: %s"), confstr)
        self._edit_config(target='running', config=confstr)

    def disable_vlan_on_trunk_int(self, vlanid, etype, interface):
        """Disable a VLAN on a trunk interface."""
        xml_etype = utils.get_xml_etype(etype)
        snippet = snipp.CMD_NO_VLAN_INT_SNIPPET
        confstr = snippet % (etype, interface, xml_etype, vlanid, xml_etype,
                             etype)
        confstr = self.create_xml_snippet(confstr)
        LOG.debug(_("NexusDriver: %s"), confstr)
        self._edit_config(target='running', config=confstr)

    def create_and_trunk_vlan(self, vlanid, etype, interface):
        """Create VLAN and trunk it on the specified ports."""
        self.create_vlan(vlanid)
        LOG.debug(_("NexusDriver created VLAN: %s"), vlanid)
        self.enable_vlan_on_trunk_int(vlanid, etype, interface)

    def delete_and_untrunk_vlan(self, vlanid, etype, interface):
        """Delete VLAN and untrunk it from the specified ports."""
        self.delete_vlan(vlanid)
        self.disable_vlan_on_trunk_int(vlanid, etype, interface)

    def get_interface_vlan_list(self, interface_name):
        """Gets expanded listing of vlans allowed on specified interface."""
        xml_sh_run_int = self._get_config(snipp.FILTER_SHOW_RUN_INT_SNIPPET
                                          % interface_name)
        return utils.get_vlan_expanded_list_for_interface(xml_sh_run_int)

    def get_span_usage(self):
        """Gets ports*vlans spanning tree instance resource usage."""
        xml_span_usage = \
            self._get_config(snipp.FILTER_SHOW_SPAN_INT_INFO_GLOBAL)
        return utils.get_span_usage(xml_span_usage)
