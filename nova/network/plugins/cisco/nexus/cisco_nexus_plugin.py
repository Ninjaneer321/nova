# Copyright 2014 ONOP psvm@onop.org
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


"""
Plugin to nova-network PSVM for Cisco nexus switch

:class: `CiscoNEXUSPlugin` implements PSVM abstract methods and manages
Nexus switch via the Cisco Nexus Driver
"""

from oslo.config import cfg

from nova.network.plugins.cisco.common import utils
from nova.network.plugins.common import psvm_plugin_base as base
from nova.openstack.common.gettextutils import _
from nova.openstack.common import importutils
from nova.openstack.common import log as logging


LOG = logging.getLogger(__name__)


cisco_nexus_plugin_opts = [
    cfg.StrOpt('psvm_driver',
               default='nova.network.plugins.cisco.nexus.'
                       'cisco_nexus_network_driver.'
                       'CiscoNEXUSDriver',
               help='Driver used to configure Nexus Switches'),
    cfg.ListOpt('psvm_ignore_vlans',
                default=[1],
                help='A list of VLANs to bypass during sync so they'
                     ' do not get inadvertently removed.'
                     'i.e. Native VLAN'),
    ]

CONF = cfg.CONF
CONF.register_opts(cisco_nexus_plugin_opts)


class CiscoNEXUSPlugin(base.PSVMPluginBase):
    """Nexus Plugin Main Class."""

    def __init__(self, **kwargs):
        self._driver = importutils.import_class(CONF.psvm_driver)
        self._driver_kwargs = kwargs

    def add_vlan_to_switch(self, interface, vlan):
        """Add specified vlan to specified switch interface."""
        interface, etype = utils.clean_interface_and_get_etype(interface)
        with self._driver(**self._driver_kwargs)\
                as driver:
            if driver is None:
                LOG.error(_("Cisco Nexus Plugin Failed: Driver failed"
                            " to connect"))
                return
            driver.create_and_trunk_vlan(vlan, etype, interface)

    def delete_vlan_from_switch(self, interface, vlan):
        """Delete specified vlan from specified switch interface."""
        interface, etype = utils.clean_interface_and_get_etype(interface)
        with self._driver(**self._driver_kwargs)\
                as driver:
            if driver is None:
                LOG.error(_("Cisco Nexus Plugin Failed: Driver failed"
                            " to connect"))
                return
            driver.disable_vlan_on_trunk_int(vlan, etype, interface)

    def sync(self, interface, networks):
        """Performs a complete sync on the switch provisioning for VLANs
           on specified interface.
        """
        _driver_kwargs = self._driver_kwargs
        _driver = self._driver
        host = _driver_kwargs['host']
        interface, etype = utils.clean_interface_and_get_etype(interface)
        interface_name = etype + interface

        def driver_create_and_trunk():
            driver.create_vlan(utils.numlist_to_string(
                vlan_missing_list[start:(end + 1)]))
            driver.enable_vlan_on_trunk_int(utils.numlist_to_string(
                vlan_missing_list[start:(end + 1)]), etype, interface)

        def driver_disable_on_trunk():
            driver.disable_vlan_on_trunk_int(utils.numlist_to_string(
                vlan_excess_list[start:(end + 1)]), etype, interface)

        with _driver(**_driver_kwargs)\
                as driver:
            if driver is None:
                LOG.error(_("Cisco Nexus Plugin Failed: Driver failed"
                            " to connect"))
                return
            interface_vlan_list = \
                set(driver.get_interface_vlan_list(interface_name))

            network_db_vlan_list = set(int(network['vlan']) for network in
                                       networks)
            keep_vlan_list = set(int(vlan) for vlan in CONF.psvm_ignore_vlans)
            vlan_missing_list = list(network_db_vlan_list -
                                     interface_vlan_list)
            vlan_excess_list = list(interface_vlan_list - network_db_vlan_list
                                    - keep_vlan_list)

            #Provision the missing vlans back onto the switch.
            if vlan_missing_list:
                vlan_missing_list = \
                    utils.numlist_to_hyphen_list(vlan_missing_list)
                limit = 400
                start = 0
                listlen = vlan_missing_list.__len__()
                subqty = listlen / limit
                end = limit - 1 if subqty > 0 else listlen - 1
                #Provision sets of 400 items at a time to overcome nexus
                #xml limitation
                for x in range(0, subqty):
                    driver_create_and_trunk()
                    start = end + 1 if end + 1 < listlen - 1 else listlen - 1
                    end = end + limit if x < subqty - 1 else listlen - 1
                #Provision last item from multiple of 400 to end or 0 to < 400
                if start != end:
                    driver_create_and_trunk()
                #Provision boundary case where start=end and mod 400=0
                elif start % limit == 0:
                    driver_create_and_trunk()

                LOG.info(_("Missing VLAN(s) %(vlan_missing_list)s synced to "
                           "switch %(host)s for interface %(interface_name)s "
                           "during this sync"), locals())

            #Remove the excess vlans from the switch
            if vlan_excess_list:
                vlan_excess_list = utils.\
                    numlist_to_hyphen_list(vlan_excess_list)
                limit = 400
                start = 0
                listlen = vlan_excess_list.__len__()
                subqty = listlen / limit
                end = limit - 1 if subqty > 0 else listlen - 1
                #Provision sets of 400 items at a time to overcome nexus
                #xml limitation
                for x in range(0, subqty):
                    driver_disable_on_trunk()
                    start = end + 1 if end + 1 < listlen - 1 else listlen - 1
                    end = end + limit if x < subqty - 1 else listlen - 1
                #Provision last item from multiple of 400 to end or 0 to < 400
                if start != end:
                    driver_disable_on_trunk()
                #Provision boundary case where start=end and mod 400=0
                elif start % limit == 0:
                    driver_disable_on_trunk()
                LOG.info(_("Excess VLAN(s) %(vlan_excess_list)s removed from "
                           "switch %(host)s interface %(interface_name)s "
                           "during this sync"), locals())
