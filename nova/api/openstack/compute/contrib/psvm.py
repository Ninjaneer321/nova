#    Copyright 2014 ONOP psvm@onop.org
#    All Rights Reserved.
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

"""The PSVM Switch API extension."""

import datetime

from webob import exc

from nova.api.openstack import extensions
from nova import exception
from nova import network
from nova.openstack.common.gettextutils import _
from nova.openstack.common import log as logging

LOG = logging.getLogger(__name__)
AUTHORIZE = extensions.extension_authorizer('compute', 'psvm')


def _get_context(req):
    return req.environ['nova.context']


def _marshall_psvm(psvm):
    _psvm = {}
    for key, value in psvm.items():
        # NOTE(danms): The original API specified non-TZ-aware timestamps
        if isinstance(value, datetime.datetime):
            value = value.replace(tzinfo=None)
        _psvm[key] = value
    return {"psvm": _psvm}


class PsvmController(object):
    """The Host Psvm API controller for the OpenStack API."""
    def __init__(self):
        self.api = network.API()

    def index(self, req):
        """Returns a list of psvms."""
        context = _get_context(req)
        AUTHORIZE(context, action='index')
        psvm = self.api.get_psvm_list(context)
        return {'psvms': [_marshall_psvm(a)['psvm']
                for a in psvm]}

    def create(self, req, body):
        """Creates an psvm, given the switch IP address and the associated
        credential id.
        """
        context = _get_context(req)
        AUTHORIZE(context, action='create')

        if len(body) != 1:
            raise exc.HTTPBadRequest()
        try:
            msg = body["psvm"]
            ip = msg["ip"]
            switch_cred_id = msg["switch_cred_id"]
        except KeyError:
            raise exc.HTTPBadRequest()

        try:
            psvm = self.api.create_psvm(context, ip, switch_cred_id)
        except Exception:
            LOG.exception(_('Hit an exception'))
            raise

        return _marshall_psvm(psvm)

    def show(self, req, id):
        """Shows the details of an psvm."""
        context = _get_context(req)
        AUTHORIZE(context, action='show')
        try:
            psvm = self.api.get_psvm(context, id)
        except exception.PSVMSwitchNotFound:
            LOG.info(_("Cannot show psvm: %s"), id)
            raise exc.HTTPNotFound()
        return _marshall_psvm(psvm)

    def update(self, req, id, body):
        """Updates the given psvm."""
        context = _get_context(req)
        AUTHORIZE(context, action='update')

        if len(body) != 1:
            raise exc.HTTPBadRequest()
        try:
            updates = body["psvm"]
        except KeyError:
            raise exc.HTTPBadRequest()

        if len(updates) < 1:
            raise exc.HTTPBadRequest()

        for key in updates.keys():
            if key not in ["ip", "switch_cred_id"]:
                raise exc.HTTPBadRequest()

        try:
            psvm = self.api.update_psvm(context, id, updates)
        except exception.PSVMSwitchNotFound:
            LOG.info(_('Cannot update psvm: %s'), id)
            raise exc.HTTPNotFound()

        return _marshall_psvm(psvm)

    def delete(self, req, id):
        """Removes an psvm by id."""
        context = _get_context(req)
        AUTHORIZE(context, action='delete')
        try:
            self.api.delete_psvm(context, id)
        except exception.PSVMSwitchNotFound:
            LOG.info(_('Cannot delete psvm: %s'), id)
            raise exc.HTTPNotFound()


class Psvm(extensions.ExtensionDescriptor):
    """Admin-only psvm administration."""

    name = "Psvm"
    alias = "os-psvm"
    namespace = "http://docs.openstack.org/compute/ext/psvm/api/v1.1"
    updated = "2012-01-12T00:00:00Z"

    def get_resources(self):
        resources = []
        res = extensions.ResourceExtension(
            'os-psvm',
            PsvmController(),
            member_actions={"action": "POST", })
        resources.append(res)
        return resources
