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

"""Tests for cisco nexus network driver"""

from oslo.config import cfg

import mock
from nova import context
from nova.network.plugins.cisco.common import cisco_constants as const
from nova.openstack.common import importutils
from nova.openstack.common import log as logging
from nova import test
from nova.tests.network import psvm_test_utils as psvmtu
import random


CISCO_NEXUS_PLUGIN_OPTS = [
    cfg.StrOpt('psvm_driver',
               default='nova.network.plugins.cisco.nexus.'
                       'cisco_nexus_network_driver.'
                       'CiscoNEXUSDriver',
               help='Driver used to configure Nexus Switches'),
]

CONF = cfg.CONF
LOG = logging.getLogger(__name__)
CONF.register_opts(CISCO_NEXUS_PLUGIN_OPTS)


class TestCiscoNexusNetworkDriver(test.TestCase):
    def setUp(self):
        super(TestCiscoNexusNetworkDriver, self).setUp()
        self.context = context.get_admin_context()
        self._drvr_kwargs = dict(host=psvmtu.rand_ip_gen(),
                                 username=psvmtu.id_lud_gen(),
                                 password=psvmtu.id_lud_gen(),
                                 device_params={"name": "nexus"})
        self._driver = importutils.import_class(CONF.psvm_driver)

    @mock.patch('ncclient.manager.connect')
    def test_creation(self, mock_nmc):
        with self._driver(**self._drvr_kwargs) as driver:
            self.assertNotEqual(driver, None)
            loginmessage = psvmtu.switch_login_messages(
                self._drvr_kwargs['username'],
                self._drvr_kwargs['device_params'],
                self._drvr_kwargs['host'],
                self._drvr_kwargs['password'])
            self.assertEqual(mock_nmc.mock_calls, [loginmessage])
        return

    @mock.patch('ncclient.manager.connect')
    def test_add_vlan(self, mock_nmc):
        with self._driver(**self._drvr_kwargs) as driver:
            self.assertNotEqual(driver, None)
            vlan = random.randrange(1, 4096)
            intf = "po101"
            driver.create_and_trunk_vlan(vlan, const.ETYPE_PORT_CHANNEL, intf)
            loginmessage = psvmtu.switch_login_messages(
                self._drvr_kwargs['username'],
                self._drvr_kwargs['device_params'],
                self._drvr_kwargs['host'],
                self._drvr_kwargs['password'])
            cvm = psvmtu.create_vlan_messages(vlan)
            avm = psvmtu.add_vlanintf_messages(vlan, intf)
            self.assertEqual(mock_nmc.mock_calls[0], loginmessage)
            self.assertEqual(mock_nmc.mock_calls[1], cvm['name'])
            self.assertEqual(mock_nmc.mock_calls[2], cvm['state'])
            self.assertEqual(mock_nmc.mock_calls[3], cvm['shutdown'])
            self.assertEqual(mock_nmc.mock_calls[4], avm)
        return

    @mock.patch('ncclient.manager.connect')
    def test_delete_vlan(self, mock_nmc):
        with self._driver(**self._drvr_kwargs) as driver:
            self.assertNotEqual(driver, None)
            vlan = random.randrange(1, 4096)
            intf = "po101"
            driver.disable_vlan_on_trunk_int(vlan, const.ETYPE_PORT_CHANNEL,
                                             intf)
            dvm = psvmtu.del_vlanintf_messages(vlan, intf)
            self.assertEqual(mock_nmc.mock_calls[1], dvm)
        return

    @mock.patch('ncclient.manager.connect')
    def test_get_interface_vlan_list(self, mock_nmc):
        connect = mock_nmc.return_value
        with self._driver(**self._drvr_kwargs) as driver:
            self.assertNotEqual(driver, None)
            intf = "po101"
            show_running_config_xml = psvmtu.get_intf_run_config_message(intf)
            show_run_int_reply = """
            <rpc-reply xmlns:ns0="http://www.cisco.com/nxos:1.0:vlan_mgr_cli"
            xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"
            xmlns:if="http://www.cisco.com/nxos:1.0:if_manager"
            xmlns:nxos="http://www.cisco.com/nxos:1.0"
            message-id="urn:uuid:2d864580-dd14-11e3-9e69-525400c15717">
              <data>
              !Command: show running-config interface port-channel100
              !Time: Fri May 16 16:07:59 2014

              version 6.0(2)N2(1)

              interface port-channel101
                description openstack2
                  switchport mode trunk
                    switchport trunk native vlan 134
                      switchport trunk allowed vlan 134,137,1601-1704,1801-1804
                        spanning-tree port type edge trunk
                          speed 1000
                            vpc 100

                            </data>
                            </rpc-reply>

            """

            connect.get.return_value = show_run_int_reply
            vlanlist = driver.get_interface_vlan_list(intf)
            self.assertEqual(mock_nmc.mock_calls[1], show_running_config_xml)
            expected_vlans = [134, 137] + range(1601, 1705) + range(1801, 1805)
            self.assertEqual(vlanlist, expected_vlans)
        return
