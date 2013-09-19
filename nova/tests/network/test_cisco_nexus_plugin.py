# Copyright 2014 ONOP psvm@onop.org
# All Rights Reserved.
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

"""Tests for cisco nexus plugin"""

from oslo.config import cfg

import mock
from nova import context
from nova.openstack.common import importutils
from nova.openstack.common import log as logging
from nova import test
from nova.tests.network import psvm_test_utils as psvmtu
import random


PSVM_OPTS = [
    cfg.StrOpt('PSVM_PLUGIN',
               default='nova.network.plugins.cisco.nexus.cisco_nexus_plugin.'
                       'CiscoNEXUSPlugin',
               help='Plugin to manage Nexus switches'),
    ]

CONF = cfg.CONF
LOG = logging.getLogger(__name__)
CONF.register_opts(PSVM_OPTS)


class TestCiscoNexusPlugin(test.TestCase):
    def setUp(self):
        super(TestCiscoNexusPlugin, self).setUp()
        self.context = context.get_admin_context()
        self.plugin_kwargs = dict(host=psvmtu.rand_ip_gen(),
                                  username=psvmtu.id_lud_gen(),
                                  password=psvmtu.id_lud_gen(),
                                 device_params={"name": "nexus"})
        self._plugin = importutils.import_object(CONF.PSVM_PLUGIN,
                                                 **self.plugin_kwargs)

    def test_plugin_import(self):
        self.assertNotEqual(self._plugin, None)

    @mock.patch('ncclient.manager.connect')
    def test_plugin_add_vlan_to_switch(self, mock_nmc):
        vlan = random.randrange(1, 4096)
        intfnum = "101"
        intf = "po" + intfnum
        self._plugin.add_vlan_to_switch(intf, vlan)
        loginmessage = psvmtu.switch_login_messages(
            self.plugin_kwargs['username'],
            self.plugin_kwargs['device_params'],
            self.plugin_kwargs['host'],
            self.plugin_kwargs['password'])
        cvm = psvmtu.create_vlan_messages(vlan)
        avm = psvmtu.add_vlanintf_messages(vlan, intfnum)
        csm = psvmtu.close_session_message()

        self.assertEqual(mock_nmc.mock_calls[0], loginmessage)
        self.assertEqual(mock_nmc.mock_calls[1], cvm['name'])
        self.assertEqual(mock_nmc.mock_calls[2], cvm['state'])
        self.assertEqual(mock_nmc.mock_calls[3], cvm['shutdown'])
        self.assertEqual(mock_nmc.mock_calls[4], avm)
        self.assertEqual(mock_nmc.mock_calls[5], csm)

    @mock.patch('ncclient.manager.connect')
    def test_plugin_delete_vlan_from_switch(self, mock_nmc):
        vlan = random.randrange(1, 4096)
        intfnum = "101"
        intf = "po" + intfnum
        self._plugin.delete_vlan_from_switch(intf, vlan)
        loginmessage = psvmtu.switch_login_messages(
            self.plugin_kwargs['username'],
            self.plugin_kwargs['device_params'],
            self.plugin_kwargs['host'],
            self.plugin_kwargs['password'])
        expectedcmd1 = psvmtu.del_vlanintf_messages(vlan, intfnum)
        expectedcmd2 = psvmtu.close_session_message()
        self.assertEqual(mock_nmc.mock_calls[0], loginmessage)
        self.assertEqual(mock_nmc.mock_calls[1], expectedcmd1)
        self.assertEqual(mock_nmc.mock_calls[2], expectedcmd2)

    @mock.patch('ncclient.manager.connect')
    def test_plugin_sync(self, mock_nmc):
        connect = mock_nmc.return_value
        connect.get.side_effect = psvmtu.connget_side_effect
        intfnum = "101"
        vlan111 = 111  # vlan is not on our intf 101
        vlan134 = 134  # vlan is on the interface
        vlan137 = 137  # vlan is on intf but not in main DB
        vlan138 = 138  # vlan is not on our intf 101
        intf = "po" + intfnum
        cvm111_138 = psvmtu.create_vlan_messages(str(vlan111) + ','
                                                 + str(vlan138))
        avm111_138 = psvmtu.add_vlanintf_messages(str(vlan111) + ','
                                                  + str(vlan138),
                                                  intfnum)
        dvm137 = psvmtu.del_vlanintf_messages(vlan137, intfnum)
        self._plugin.sync(intf,
                          list([dict(vlan=vlan111),
                               dict(vlan=vlan134),
                               dict(vlan=vlan138)]))
        self.assertEqual(mock_nmc.mock_calls[0],
                         psvmtu.switch_login_messages(
                             self.plugin_kwargs['username'],
                             self.plugin_kwargs['device_params'],
                             self.plugin_kwargs['host'],
                             self.plugin_kwargs['password']))
        self.assertEqual(mock_nmc.mock_calls[1],
                         psvmtu.get_intf_run_config_message('port-channel'
                                                            + str(intfnum)))
        # self.assertEqual(mock_nmc.mock_calls[2], psvmtu.show_vbr_message())
        #print mock_nmc.mock_calls[2]
        #self.assertEqual(0, 1)
        self.assertEqual(mock_nmc.mock_calls[2], cvm111_138['name'])
        self.assertEqual(mock_nmc.mock_calls[3], cvm111_138['state'])
        self.assertEqual(mock_nmc.mock_calls[4], cvm111_138['shutdown'])
        self.assertEqual(mock_nmc.mock_calls[5], avm111_138)
        self.assertEqual(mock_nmc.mock_calls[6], dvm137)
        self.assertEqual(mock_nmc.mock_calls[7],
                         psvmtu.close_session_message())
