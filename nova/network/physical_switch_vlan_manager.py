# Copyright 2014 ONOP psvm@onop.org
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


"""
Physcial Switch VLAN Manager (PSVM)
requires psvm=true flag in /etc/nova/nova.conf

:class:`PhysicalSwitchVlanManager` links the nova-network
linux_net LinuxBridge plug/unplug functionality to physical
switch plugins/drivers to maintain end to end management
of the underlying network plumbing.
"""

import socket

from oslo.config import cfg

import nova.context
from nova import exception
from nova.objects import network as network_obj
from nova.objects import psvm as psvm_obj
from nova.objects import psvmcred as psvmcred_obj
from nova.objects import psvmpbind as psvmpbind_obj
from nova.openstack.common.gettextutils import _
from nova.openstack.common import importutils
from nova.openstack.common import log as logging


LOG = logging.getLogger(__name__)


psvm_opts = [
    cfg.StrOpt('psvm_plugin',
               default='nova.network.plugins.cisco.nexus.cisco_nexus_plugin.'
                       'CiscoNEXUSPlugin',
               help='Plugin to manage Nexus switches'),
    ]

CONF = cfg.CONF
CONF.register_opts(psvm_opts)


class PhysicalSwitchVlanManager(object):

    def __init__(self):
        self.context = nova.context.get_admin_context()

    def __enter__(self):
        try:
            self._setup()
        except exception.NotFound as e:
            LOG.exception(_("PSVM: Setup failed for host %(hostname)s "
                            "%(e)s"), {'hostname': self.hostname, 'e': e})
            return None
        except Exception:
            raise
        LOG.debug(_("PSVM: SETUP COMPLETE"))
        return self

    def __exit__(self, type, value, traceback):
        pass

    def _setup(self):
        self.hostname = socket.gethostname()
        self.fqdn = socket.getfqdn()
        self.sw_binds = psvmpbind_obj.PsvmpbindList.get_by_host(self.context,
                                                                self.fqdn)

    def _get_switch_details(self, sw_bind):
        _switch_id = sw_bind['switch_id']
        _switch_port = sw_bind['switch_port']
        _switch = psvm_obj.Psvm.get_by_id(self.context, _switch_id)
        _switch_ip = _switch['ip']
        _switch_cred_id = _switch['switch_cred_id']
        _switch_cred = psvmcred_obj.Psvmcred.get_by_id(self.context,
                                                       _switch_cred_id)
        _user_name = _switch_cred['user_name']
        _password = _switch_cred['password']
        plugin_kwargs = dict(host=_switch_ip,
                             username=_user_name,
                             password=_password)
        _plugin = importutils.import_object(CONF.psvm_plugin, **plugin_kwargs)
        return _plugin, _switch_port

    def add_vlan_to_switch(self, vlan_id):
        def do_add_vlan_to_switch(sw_bind):
            _plugin, _switch_port = self._get_switch_details(sw_bind)
            self._add_vlan_to_switch(vlan_id, _plugin, _switch_port)

        for sw_bind in self.sw_binds:
            do_add_vlan_to_switch(sw_bind)

    def _add_vlan_to_switch(self, vlan_id, plugin, switch_port):
        try:
            plugin.add_vlan_to_switch(switch_port, vlan_id)
        except Exception as e:
            LOG.exception(_("PSVM: Failed to provision VLAN %(vlan_id)s "
                            "for host %(hostname)s"),
                          {'vlan_id': vlan_id, 'hostname': self.hostname})
            raise exception.PhysicalSwitchVlanManagerError(e)

    def delete_vlan_from_switch(self, vlan_id):
        def do_delete_vlan_from_switch(sw_bind):
            _plugin, _switch_port = self._get_switch_details(sw_bind)
            self._delete_vlan_from_switch(vlan_id, _plugin, _switch_port)

        for sw_bind in self.sw_binds:
            do_delete_vlan_from_switch(sw_bind)

    def _delete_vlan_from_switch(self, vlan_id, plugin, switch_port):
        try:
            plugin.delete_vlan_from_switch(switch_port, vlan_id)
        except Exception as e:
            LOG.exception(_("PSVM: Failed to deprovision VLAN %(vlan_id)s "
                            "for host %(hostname)s"),
                          {'vlan_id': vlan_id, 'hostname': self.hostname})
            raise exception.PhysicalSwitchVlanManagerError(e)

    def sync_physical_network(self):
        def do_sync_physical_network(sw_bind, networks):
            _plugin, _switch_port = self._get_switch_details(sw_bind)
            self._sync_physical_network(networks, _plugin, _switch_port)

        networks = network_obj.NetworkList.get_by_host(self.context,
                                                       self.hostname)

        for sw_bind in self.sw_binds:
            do_sync_physical_network(sw_bind, networks)

    def _sync_physical_network(self, networks, plugin, switch_port):
        try:
            plugin.sync(switch_port, networks)
        except Exception as e:
            LOG.exception(_("PSVM: Failed to sync networks"
                            "for host %(hostname)s"),
                          {'hostname': self.hostname})
            raise exception.PhysicalSwitchVlanManagerError(e)
