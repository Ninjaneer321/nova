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

"""Tests utilities for physical switch vlan manager test code and cisco nexus
plugin/deiver"""


import mock
import random
import string


SHOW_RUN_INT_REPLY = """
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
          switchport trunk allowed vlan 134,137
            spanning-tree port type edge trunk
              speed 1000
                vpc 100

                </data>
                </rpc-reply>

"""


SHOW_VBR_REPLY = """
<rpc-reply xmlns:ns0="http://www.cisco.com/nxos:1.0:vlan_mgr_cli"
xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"
xmlns:if="http://www.cisco.com/nxos:1.0:if_manager"
xmlns:nxos="http://www.cisco.com/nxos:1.0"
message-id="urn:uuid:2d864580-dd14-11e3-9e69-525400c15717">
  <data>
   <show>
    <vlan>
     <brief>
      <__XML__OPT_Cmd_show_vlan_brief___readonly__>
       <__readonly__>
        <TABLE_vlanbriefxbrief>
         <ROW_vlanbriefxbrief>
          <vlanshowbr-vlanid>1</vlanshowbr-vlanid>
          <vlanshowbr-vlanid-utf>1</vlanshowbr-vlanid-utf>
          <vlanshowbr-vlanname>default</vlanshowbr-vlanname>
          <vlanshowbr-vlanstate>active</vlanshowbr-vlanstate>
          <vlanshowbr-shutstate>noshutdown</vlanshowbr-shutstate>
          """ + \
          """
          <vlanshowplist-ifidx>port-channel127-128,""" + \
          """Ethernet1/3-4,Ethernet1/7-28,Ethernet3/1-32,""" + \
          """Ethernet100/1/1,Ethernet100/1/2-6""" + \
          """</vlanshowplist-ifidx>
          <vlanshowplist-ifidx>Ethernet100/1/7-16,""" + \
          """Ethernet100/1/19-32</vlanshowplist-ifidx>
         </ROW_vlanbriefxbrief>
         <ROW_vlanbriefxbrief>
          <vlanshowbr-vlanid>127</vlanshowbr-vlanid>
          <vlanshowbr-vlanid-utf>127</vlanshowbr-vlanid-utf>
          <vlanshowbr-vlanname>mgmt</vlanshowbr-vlanname>
          <vlanshowbr-vlanstate>active</vlanshowbr-vlanstate>
          <vlanshowbr-shutstate>noshutdown</vlanshowbr-shutstate>
          <vlanshowplist-ifidx>port-channel1,""" +\
          """port-channel127-128,Ethernet1/31-32,""" + \
          """Ethernet3/1-32</vlanshowplist-ifidx>
         </ROW_vlanbriefxbrief>
         <ROW_vlanbriefxbrief>
          <vlanshowbr-vlanid>134</vlanshowbr-vlanid>
          <vlanshowbr-vlanid-utf>134</vlanshowbr-vlanid-utf>
          <vlanshowbr-vlanname>pub-float</vlanshowbr-vlanname>
          <vlanshowbr-vlanstate>active</vlanshowbr-vlanstate>
          <vlanshowbr-shutstate>noshutdown</vlanshowbr-shutstate>
          <vlanshowplist-ifidx>port-channel1,port-channel10,""" + \
          """port-channel100-101,port-channel127-128,""" + \
          """Ethernet1/1,Ethernet1/31-32,Ethernet3/1-32,""" + \
          """Ethernet100/1/17,Ethernet100/1/18""" + \
          """</vlanshowplist-ifidx>
         </ROW_vlanbriefxbrief>
         <ROW_vlanbriefxbrief>
          <vlanshowbr-vlanid>137</vlanshowbr-vlanid>
          <vlanshowbr-vlanid-utf>137</vlanshowbr-vlanid-utf>
          <vlanshowbr-vlanname>pub-float</vlanshowbr-vlanname>
          <vlanshowbr-vlanstate>active</vlanshowbr-vlanstate>
          <vlanshowbr-shutstate>noshutdown</vlanshowbr-shutstate>
          <vlanshowplist-ifidx>port-channel1,port-channel10,""" + \
          """port-channel100-101,port-channel127-128,""" + \
          """Ethernet1/1,Ethernet1/31-32,Ethernet3/1-32,""" + \
          """Ethernet100/1/17,Ethernet100/1/18""" + \
          """</vlanshowplist-ifidx>
         </ROW_vlanbriefxbrief>
         <ROW_vlanbriefxbrief>
          <vlanshowbr-vlanid>138</vlanshowbr-vlanid>
          <vlanshowbr-vlanid-utf>138</vlanshowbr-vlanid-utf>
          <vlanshowbr-vlanname>pub-float</vlanshowbr-vlanname>
          <vlanshowbr-vlanstate>active</vlanshowbr-vlanstate>
          <vlanshowbr-shutstate>noshutdown</vlanshowbr-shutstate>
          <vlanshowplist-ifidx>port-channel1,port-channel10,""" + \
          """port-channel100,port-channel127-128,""" + \
          """Ethernet1/1,Ethernet1/31-32,Ethernet3/1-32,""" + \
          """Ethernet100/1/17,Ethernet100/1/18""" + \
          """</vlanshowplist-ifidx>
         </ROW_vlanbriefxbrief>
        </TABLE_vlanbriefxbrief>
       </__readonly__>
      </__XML__OPT_Cmd_show_vlan_brief___readonly__>
     </brief>
    </vlan>
   </show>
  </data>
 </rpc-reply>
 """


#Generate a random alphanumeric string having lower, upper, digits
def id_lud_gen(size=6, chars=string.ascii_lowercase +
               string.ascii_uppercase +
               string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


#Generate a random valid IP address
def rand_ip_gen():
    not_valid = [10, 127, 169, 172, 192]

    first = random.randrange(1, 256)
    while first in not_valid:
        first = random.randrange(1, 256)

    ip = ".".join([str(first), str(random.randrange(1, 256)),
                   str(random.randrange(1, 256)),
                   str(random.randrange(1, 256))])

    return ip


def switch_login_messages(usr, dp, hst, psw):
    return mock.call(username=usr, device_params=dp, host=hst,
                     password=psw, port=22)


def show_vbr_message():
    return mock.call().get(('subtree', '\n      '
        '<show xmlns="http://www.cisco.com/nxos:1.0:vlan_mgr_cli">\n'
        '        <vlan>\n'
        '          <brief/>\n'
        '        </vlan>\n'
        '      </show>\n'))


def create_vlan_messages(vlan):
    name = mock.call().edit_config(target='running',
            config='\n      <config xmlns:xc="urn:ietf:params:xml:'
            'ns:netconf:base:1.0">'
            '\n        <configure>'
            '\n          <__XML__MODE__exec_configure>'
            '\n            <vlan>'
            '\n              <vlan-id-create-delete>'
            '\n                <__XML__PARAM_value>'
            + str(vlan) + '</__XML__PARAM_value>'
            '\n                <__XML__MODE_vlan>'
            '\n                </__XML__MODE_vlan>'
            '\n              </vlan-id-create-delete>'
            '\n            </vlan>\n'
            '\n          </__XML__MODE__exec_configure>'
            '\n        </configure>'
            '\n      </config>\n')
    state = mock.call().edit_config(target='running',
            config='\n      <config xmlns:xc='
            '"urn:ietf:params:xml:ns:netconf:base:1.0">'
            '\n        <configure>'
            '\n          <__XML__MODE__exec_configure>'
            '\n            <vlan>'
            '\n              <vlan-id-create-delete>'
            '\n                <__XML__PARAM_value>'
            + str(vlan) + '</__XML__PARAM_value>'
            '\n                <__XML__MODE_vlan>'
            '\n                  <state>'
            '\n                    <vstate>active</vstate>'
            '\n                  </state>'
            '\n                </__XML__MODE_vlan>'
            '\n              </vlan-id-create-delete>'
            '\n            </vlan>\n'
            '\n          </__XML__MODE__exec_configure>'
            '\n        </configure>'
            '\n      </config>\n')
    shutdown = mock.call().edit_config(target='running',
            config='\n      <config xmlns:xc='
            '"urn:ietf:params:xml:ns:netconf:base:1.0">'
            '\n        <configure>'
            '\n          <__XML__MODE__exec_configure>'
            '\n            <vlan>'
            '\n              <vlan-id-create-delete>'
            '\n                <__XML__PARAM_value>'
            + str(vlan) + '</__XML__PARAM_value>'
            '\n                <__XML__MODE_vlan>'
            '\n                  <no>'
            '\n                    <shutdown/>'
            '\n                  </no>'
            '\n                </__XML__MODE_vlan>'
            '\n              </vlan-id-create-delete>'
            '\n            </vlan>\n'
            '\n          </__XML__MODE__exec_configure>'
            '\n        </configure>'
            '\n      </config>\n')
    return {'name': name, 'state': state, 'shutdown': shutdown}


def add_vlanintf_messages(vlan, intfnum):
    return mock.call().edit_config(target='running',
            config='\n      <config xmlns:xc='
            '"urn:ietf:params:xml:ns:netconf:base:1.0">'
            '\n        <configure>'
            '\n          <__XML__MODE__exec_configure>'
            '\n          <interface>'
            '\n            <port-channel>'
            '\n              <interface>' + intfnum + '</interface>'
            '\n              <__XML__MODE_if-eth-port-'
            'channel-switch>'
            '\n                <switchport>'
            '\n                  <trunk>'
            '\n                    <allowed>'
            '\n                      <vlan>'
            '\n                        <add>'
            '\n                          <add-vlans>'
            + str(vlan) + '</add-vlans>'
            '\n                        </add>'
            '\n                      </vlan>'
            '\n                    </allowed>'
            '\n                  </trunk>'
            '\n                </switchport>'
            '\n              </__XML__MODE_if-eth-port-'
            'channel-switch>'
            '\n            </port-channel>'
            '\n          </interface>\n'
            '\n          </__XML__MODE__exec_configure>'
            '\n        </configure>'
            '\n      </config>\n')


def del_vlanintf_messages(vlan, intfnum):
    return mock.call().edit_config(target='running', config='\n      '
            '<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">'
            '\n        <configure>'
            '\n          <__XML__MODE__exec_configure>'
            '\n          <interface>'
            '\n            <port-channel>'
            '\n              <interface>' + intfnum + '</interface>'
            '\n              <__XML__MODE_if-eth-port-channel-switch>'
            '\n                <switchport>'
            '\n                  <trunk>'
            '\n                    <allowed>'
            '\n                      <vlan>'
            '\n                        <remove>'
            '\n                          <remove-vlans>'
            + str(vlan) + '</remove-vlans>'
            '\n                        </remove>'
            '\n                      </vlan>'
            '\n                    </allowed>'
            '\n                  </trunk>'
            '\n                </switchport>'
            '\n              </__XML__MODE_if-eth-port-channel-switch>'
            '\n            </port-channel>'
            '\n          </interface>\n'
            '\n          </__XML__MODE__exec_configure>'
            '\n        </configure>'
            '\n      </config>\n')


def get_intf_run_config_message(intf):
    return mock.call().get(('subtree', '\n      '
            '<show xmlns="http://www.cisco.com/nxos:1.0:vlan_mgr_cli">\n'
            '        <running-config>\n''          <interface/>\n'
            '            <interface>' + intf + '</interface>\n'
            '        </running-config>\n'
            '      </show>\n'))


def get_call_get(xyz):
    return mock.call().get(xyz)


def close_session_message():
    return mock.call().close_session()


def connget_side_effect(*args):
    if get_call_get(args[0]) == get_intf_run_config_message('port-channel'
                                                            + str(101)):
        return SHOW_RUN_INT_REPLY
    elif get_call_get(args[0]) == show_vbr_message():
        return SHOW_VBR_REPLY
    else:
        print("UNEXPECTED INPUT")
        print(args[0])
        return "UNEXPECTED INPUT"
