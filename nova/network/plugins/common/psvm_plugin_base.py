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
PSVM Plug-in API specification.

:class:`PSVMPluginBase` provides the definition of minimum set of
methods that needs to be implemented by a PSVM Plug-in.
"""

from nova.openstack.common import log as logging

import abc
import six


LOG = logging.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class PSVMPluginBase(object):

    @abc.abstractmethod
    def add_vlan_to_switch(self, interface, vlan):
        """Ensures VLAN is provisioned on switch and interface.

        Connects to switch, creates VLAN if needed, and adds to
        specified interface

        :param interface: interface name i.e. ethernet1/1 or port-channel10
        :param vlan: vlan id: range 1-4094 excluding switch specific
        reserved vlans
        """
        pass

    @abc.abstractmethod
    def delete_vlan_from_switch(self, interface, vlan):
        """Removes VLAN provisioned on interface.

        Connects to switch, removes VLAN from specified interface

        :param interface: interface name i.e. ethernet1/1 or port-channel10
        :param vlan: vlan id: range 1-4094 excluding switch specific
        reserved vlans
        """
        pass

    @abc.abstractmethod
    def sync(self, interface, networks):
        """Syncs Vlan information for host connected to interface.

        Connects to switch, retrieves VLAN information, corrects
        discrepancies

        :param interface: interface name i.e. ethernet1/1 or port-channel10
        :param vlan: vlan id: range 1-4094 excluding switch specific
        reserved vlans
        """
        pass
