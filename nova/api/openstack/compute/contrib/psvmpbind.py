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
from nova import utils

LOG = logging.getLogger(__name__)
AUTHORIZE = extensions.extension_authorizer('compute', 'psvmpbind')


def _get_context(req):
    return req.environ['nova.context']


def get_host_from_body(fn):
    """Makes sure that the host exists."""
    def wrapped(self, req, id, body, *args, **kwargs):
        if len(body) == 1 and "host" in body:
            host = body['host']
        else:
            raise exc.HTTPBadRequest()
        return fn(self, req, id, host, *args, **kwargs)
    return wrapped


def _marshall_psvmpbind(psvmpbind):
    _psvmpbind = {}
    for key, value in psvmpbind.items():
        # NOTE(danms): The original API specified non-TZ-aware timestamps
        if isinstance(value, datetime.datetime):
            value = value.replace(tzinfo=None)
        _psvmpbind[key] = value
    return {"psvmpbind": _psvmpbind}


class PsvmpbindController(object):
    """The Host Psvmpbind API controller for the OpenStack API."""
    def __init__(self):
        self.api = network.API()

    def index(self, req):
        """Returns a list of psvmpbind's."""
        context = _get_context(req)
        AUTHORIZE(context, action='index')
        psvmpbind = self.api.get_psvmpbind_list(context)
        return {'psvmpbinds': [_marshall_psvmpbind(a)['psvmpbind']
                for a in psvmpbind]}

    def create(self, req, body):
        """Creates an psvmpbind, given the associated switch_id
           compute_node_id and switch_port.
        """
        context = _get_context(req)
        AUTHORIZE(context, action='create')

        if len(body) != 1:
            raise exc.HTTPBadRequest()
        try:
            msg = body["psvmpbind"]
            switch_id = msg["switch_id"]
            compute_node_id = msg["compute_node_id"]
            switch_port = msg["switch_port"]
        except KeyError:
            raise exc.HTTPBadRequest()
        try:
            utils.check_string_length(switch_port,
                                      "Psvmpbind switch_port",
                                      1, 255)
        except exception.InvalidInput as e:
            raise exc.HTTPBadRequest(explanation=e.format_message())

        try:
            psvmpbind = self.api.create_psvmpbind(context, switch_id,
                                                  compute_node_id,
                                                  switch_port)
        except Exception:
            LOG.exception(_('Hit an exception'))
            raise

        return _marshall_psvmpbind(psvmpbind)

    def show(self, req, id):
        """Shows the details of a psvmpbind."""
        context = _get_context(req)
        AUTHORIZE(context, action='show')
        try:
            psvmpbind = self.api.get_psvmpbind(context, id)
        except exception.PSVMSwitchportBindingNotFound:
            LOG.info(_("Cannot show psvm switch port binding: %s"), id)
            raise exc.HTTPNotFound()
        return _marshall_psvmpbind(psvmpbind)

    def update(self, req, id, body):
        """Updates either the switch_id, compute_node_id or switch_port of a
        given psvmpbind.
        """
        context = _get_context(req)
        AUTHORIZE(context, action='update')

        if len(body) != 1:
            raise exc.HTTPBadRequest()
        try:
            updates = body["psvmpbind"]
        except KeyError:
            raise exc.HTTPBadRequest()

        if len(updates) < 1:
            raise exc.HTTPBadRequest()

        for key in updates.keys():
            if key not in ["switch_id", "compute_node_id", "switch_port"]:
                raise exc.HTTPBadRequest()

        try:
            if 'switch_port' in updates:
                utils.check_string_length(updates['switch_port'],
                                          "Psvmpbind switch_port",
                                          1, 255)
        except exception.InvalidInput as e:
            raise exc.HTTPBadRequest(explanation=e.format_message())

        try:
            psvmpbind = self.api.update_psvmpbind(context, id, updates)
        except exception.PSVMSwitchportBindingNotFound:
            LOG.info(_("Cannot update psvm switch port binding: %s"), id)
            raise exc.HTTPNotFound()

        return _marshall_psvmpbind(
            psvmpbind)

    def delete(self, req, id):
        """Removes an psvmpbind by id."""
        context = _get_context(req)
        AUTHORIZE(context, action='delete')
        try:
            self.api.delete_psvmpbind(context, id)
        except exception.PSVMSwitchportBindingNotFound:
            LOG.info(_("Cannot delete psvm switch port binding: %s"), id)
            raise exc.HTTPNotFound()


class Psvmpbind(extensions.ExtensionDescriptor):
    """Admin-only psvmpbind administration."""

    name = "Psvmpbind"
    alias = "os-psvmpbind"
    namespace = "http://docs.openstack.org/compute/ext/psvmpbind/api/v1.1"
    updated = "2012-01-12T00:00:00Z"

    def get_resources(self):
        resources = []
        res = extensions.ResourceExtension(
            'os-psvmpbind',
            PsvmpbindController(),
            member_actions={"action": "POST", })
        resources.append(res)
        return resources
