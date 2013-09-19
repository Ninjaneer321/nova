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
#


"""
common utilities for cisco plugin
"""

from lxml import etree
from nova.network.plugins.cisco.common import cisco_constants as const
from nova.network.plugins.cisco.common import cisco_exceptions as cexc
from nova.network.plugins.cisco.nexus import cisco_nexus_snippets as snipp
from nova.openstack.common.gettextutils import _
from nova.openstack.common import log as logging
import re
import StringIO

LOG = logging.getLogger(__name__)


def get_vlan_expanded_list_for_interface(xml_sh_run_int):
    """Expand out VLAN listing by removing hyphens and appending to list."""
    tree = etree.parse(StringIO.StringIO(xml_sh_run_int))
    prefixmap = {'f': "urn:ietf:params:xml:ns:netconf:base:1.0"}
    tag = "data"
    find = etree.XPath('//f:' + tag, namespaces=prefixmap)
    searchlist = find(tree)
    vlan_allow_line = 'switchport trunk allowed vlan'
    for item in searchlist:
        interface_config = item.text
        for line in interface_config.splitlines():
            if vlan_allow_line in line:
                first, sep, last = line.rpartition(vlan_allow_line)
                vlan_list = last.strip().split(',')
    vlan_exp_list = []
    for vlan in vlan_list:
        if '-' in vlan:
            start, sep, end = vlan.partition('-')
            vlan_exp_list = vlan_exp_list + range(int(start), int(end) + 1)
        else:
            if vlan != 'none':
                vlan_exp_list.append(int(vlan))
    return vlan_exp_list


def get_span_usage(xml_span_usage):
    """Gets current spanning tree logical interface resource usage."""
    tree = etree.parse(StringIO.StringIO(xml_span_usage))
    prefixmap = {'f': "urn:ietf:params:xml:ns:netconf:base:1.0"}
    tag = "data"
    find = etree.XPath('//f:' + tag, namespaces=prefixmap)
    searchlist = find(tree)
    line_search_pattern = 'Total ports*vlans'
    for item in searchlist:
        interface_config = item.text
        for line in interface_config.splitlines():
            if line_search_pattern in line:
                return line.split(':')[-1].strip()


def numlist_to_hyphen_list(number_list):
    """Converts number list into a sorted duplicate free hyphenated string."""
    number_list = list(set(number_list))
    number_list.sort()
    flag = 0
    new_list = []
    number_list_len = number_list.__len__()
    first_num = 0
    last_num = 0
    for num in number_list:
        num_index_current = number_list.index(num)
        num_index_next = num_index_current + 1 \
            if num_index_current < number_list_len - 1 else None
        if num_index_next is not None:
            if num + 1 == number_list[num_index_next]:
                if flag == 0:
                    first_num = num
                flag = 1
            elif flag == 1:
                last_num = num
                num = '%s-%s' % (str(first_num), str(last_num))
                first_num = 0
                last_num = 0
                flag = 0
        elif first_num != 0:
            last_num = num
            num = '%s-%s' % (str(first_num), str(last_num))
            flag = 0
        if flag == 0:
            new_list.append(num)
    return new_list


def numlist_to_string(number_list):
    """Converts number list into a string."""
    num_string_list = [str(x) for x in number_list]
    num_string = ','.join(num_string_list)
    return num_string


def get_xml_etype(etype):
    """Translate etype into XML etype."""
    if (etype == const.ETYPE_ETHERNET):
        xml_etype = snipp.ETYPE_ETHERNET
    elif (etype == const.ETYPE_PORT_CHANNEL):
        xml_etype = snipp.ETYPE_PORT_CHANNEL
    else:
        LOG.error(_("Unsupported etype. Should not reach here."))
        raise
    return xml_etype


def clean_interface_and_get_etype(interface):
    """Clean and separate out interface and etype."""
    #etype contains alpha chars only
    etype = re.sub('[0-9/]', '', interface).lower()
    #interface contains numeric, hyphen, forward slash only
    interface = re.sub('[^0-9/]', '', interface)
    if etype.startswith('p'):
        etype = const.ETYPE_PORT_CHANNEL
    elif etype.startswith('e'):
        etype = const.ETYPE_ETHERNET
    else:
        LOG.error(_("Unsupported interface type of %s"), etype)
        raise cexc.CiscoNEXUSUnsupportedEtype(etype=etype)
    return interface, etype
