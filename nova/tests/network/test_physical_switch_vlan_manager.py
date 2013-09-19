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

"""Tests for network physical_switch_vlan_manager"""

import mock
from nova import context
from nova import db
from nova.network import physical_switch_vlan_manager as psvm
from nova.openstack.common import log as logging
from nova import test
from nova.tests.network import psvm_test_utils as psvmtu
import random


LOG = logging.getLogger(__name__)


class TestPhysicalSwitchVlanManager(test.TestCase):
    def setUp(self):
        super(TestPhysicalSwitchVlanManager, self).setUp()
        self.context = context.get_admin_context()
        self.scred_ref = db.switch_cred_create(self.context,
                                               dict(user_name=
                                                    psvmtu.id_lud_gen(),
                                                    password=
                                                    psvmtu.id_lud_gen(),
                                                    device_params={"name":
                                                                   "nexus"}))
        self.switch1_ref = db.\
            switch_create(self.context,
                          dict(ip=psvmtu.rand_ip_gen(),
                               switch_cred_id=self.scred_ref['id']))
        self.switch2_ref = db.\
            switch_create(self.context,
                          dict(ip=psvmtu.rand_ip_gen(),
                               switch_cred_id=self.scred_ref['id']))

        s_ref = db.service_create(self.context,
                                  {'host': 'dummy', 'binary': 'nova-compute',
                                   'topic': 'compute', 'report_count': 0,
                                   'availability_zone': 'dummyzone'})

        self.cnode_param = {'service_id': s_ref['id'],
                            'vcpus': 4, 'memory_mb': 7909, 'local_gb': 240,
                            'vcpus_used': 0, 'memory_mb_used': 512,
                            'local_gb_used': 0,
                            'hypervisor_type': 'QEMU',
                            'hypervisor_version': 1000000,
                            'cpu_info': '{"vendor": "Intel",\
                                          "model": "Westmere",\
                                          "arch": "x86_64"}',
                            'hypervisor_hostname': 'test_openstack',
                            'free_ram_mb': 1024, 'free_disk_gb': 240,
                            'current_workload': 0, 'running_vms': 0,
                            'disk_available_least': 171,
                            'host_ip': '127.0.0.1',
                            'supported_instances': '',
                            'metrics': '', 'pci_stats': '',
                            'extra_resources': '',
                            'stats': ''}
        self.cnode_ref = db.compute_node_create(self.context, self.cnode_param)
        self.portprefix = 'po'
        self.portnum = '101'
        self.spb_ref1 = db.\
            switchport_binding_create(self.context,
                                      dict(switch_id=self.switch1_ref['id'],
                                           compute_node_id=self.
                                           cnode_ref['id'],
                                           switch_port=self.portprefix
                                           + self.portnum))
        self.spb_ref2 = db.\
            switchport_binding_create(self.context,
                                      dict(switch_id=self.
                                           switch2_ref['id'],
                                           compute_node_id=self.
                                           cnode_ref['id'],
                                           switch_port=self.portprefix
                                           + self.portnum))

    @mock.patch('ncclient.manager.connect')
    def test_add_vlan_to_switch(self, mock_nmc):
        p = mock.patch('socket.gethostname',
                       new=mock.MagicMock(return_value=self.
                                          cnode_param['hypervisor_hostname']))
        p.start()

        vlan = random.randrange(1, 4096)
        lg1msg = psvmtu.switch_login_messages(self.scred_ref['user_name'],
                                              self.scred_ref['device_params'],
                                              self.switch1_ref['ip'],
                                              self.scred_ref['password'])
        lg2msg = psvmtu.switch_login_messages(self.scred_ref['user_name'],
                                              self.scred_ref['device_params'],
                                              self.switch2_ref['ip'],
                                              self.scred_ref['password'])
        cvm = psvmtu.create_vlan_messages(vlan)
        avm = psvmtu.add_vlanintf_messages(vlan, self.portnum)
        csm = psvmtu.close_session_message()

        with psvm.PhysicalSwitchVlanManager() as self_psvm:
            self.assertNotEqual(self_psvm, None)

            self_psvm.add_vlan_to_switch(vlan)

            expectedcmds = [lg1msg, cvm['name'], cvm['state'],
                            cvm['shutdown'], avm, csm,
                            lg2msg, cvm['name'], cvm['state'],
                            cvm['shutdown'], avm, csm]
            self.assertEqual(mock_nmc.mock_calls, expectedcmds)
        p.stop()

    @mock.patch('ncclient.manager.connect')
    def test_delete_vlan_to_switch(self, mock_nmc):
        p = mock.patch('socket.gethostname',
                       new=mock.MagicMock(return_value=self.
                                          cnode_param['hypervisor_hostname']))
        p.start()

        vlan = random.randrange(1, 4096)
        lg1msg = psvmtu.switch_login_messages(self.scred_ref['user_name'],
                                              self.scred_ref['device_params'],
                                              self.switch1_ref['ip'],
                                              self.scred_ref['password'])
        lg2msg = psvmtu.switch_login_messages(self.scred_ref['user_name'],
                                              self.scred_ref['device_params'],
                                              self.switch2_ref['ip'],
                                              self.scred_ref['password'])
        dvm = psvmtu.del_vlanintf_messages(vlan, self.portnum)
        csm = psvmtu.close_session_message()

        with psvm.PhysicalSwitchVlanManager() as self_psvm:
            self.assertNotEqual(self_psvm, None)

            self_psvm.delete_vlan_from_switch(vlan)

            expectedcmds = [lg1msg, dvm, csm,
                            lg2msg, dvm, csm]
            self.assertEqual(mock_nmc.mock_calls, expectedcmds)

        p.stop()

    @mock.patch('ncclient.manager.connect')
    def test_sync_physical_network(self, mock_nmc):
        p = mock.patch('socket.gethostname',
                       new=mock.MagicMock(return_value=self.
                                          cnode_param['hypervisor_hostname']))
        p.start()

        connect = mock_nmc.return_value
        connect.get.side_effect = psvmtu.connget_side_effect

        intfnum = "101"
        vlan111 = 111  # vlan is not on our intf 101
        vlan134 = 134  # vlan is on the interface
        vlan137 = 137  # vlan is on intf but not in main DB
        vlan138 = 138  # vlan is not on our intf 101
        lg1msg = psvmtu.switch_login_messages(self.scred_ref['user_name'],
                                              self.scred_ref['device_params'],
                                              self.switch1_ref['ip'],
                                              self.scred_ref['password'])
        lg2msg = psvmtu.switch_login_messages(self.scred_ref['user_name'],
                                              self.scred_ref['device_params'],
                                              self.switch2_ref['ip'],
                                              self.scred_ref['password'])
        ircm = psvmtu.get_intf_run_config_message('port-channel' +
                                                  str(intfnum))
        cvm111_138 = psvmtu.create_vlan_messages(str(vlan111) + ',' +
                                                 str(vlan138))
        avm111_138 = psvmtu.add_vlanintf_messages(str(vlan111) + ',' +
                                                  str(vlan138),
                                                  intfnum)
        dvm137 = psvmtu.del_vlanintf_messages(vlan137, intfnum)

        with psvm.PhysicalSwitchVlanManager() as self_psvm:
            self.assertNotEqual(self_psvm, None)

            p2 = mock.patch('nova.objects.network.NetworkList.get_by_host',
                            new=mock.MagicMock(
                                return_value=list([dict(vlan=vlan111),
                                                   dict(vlan=vlan134),
                                                   dict(vlan=vlan138)])))
            p2.start()

            self_psvm.sync_physical_network()

            expectedcmds = [lg1msg, ircm,
                            cvm111_138['name'], cvm111_138['state'],
                            cvm111_138['shutdown'],
                            avm111_138, dvm137, psvmtu.close_session_message(),
                            lg2msg, ircm,
                            cvm111_138['name'], cvm111_138['state'],
                            cvm111_138['shutdown'],
                            avm111_138, dvm137, psvmtu.close_session_message()]
            self.assertEqual(mock_nmc.mock_calls, expectedcmds)
            p2.stop()

        p.stop()
