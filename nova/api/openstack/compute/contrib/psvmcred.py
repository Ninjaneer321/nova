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
AUTHORIZE = extensions.extension_authorizer('compute', 'psvmcred')


def _get_context(req):
    return req.environ['nova.context']


class PsvmcredController(object):
    """The Host Psvmcred API controller for the OpenStack API."""
    def __init__(self):
        self.api = network.API()

    def index(self, req):
        """Returns a list of psvmcreds."""
        context = _get_context(req)
        AUTHORIZE(context, action='index')
        psvmcred = self.api.get_psvmcred_list(context)
        return {'psvmcreds': [self._marshall_psvmcred(a)['psvmcred']
                for a in psvmcred]}

    def create(self, req, body):
        """Creates an psvmcred, given a user_name and password."""
        context = _get_context(req)
        AUTHORIZE(context, action='create')

        if len(body) != 1:
            raise exc.HTTPBadRequest()
        try:
            host_psvmcred = body["psvmcred"]
            user_name = host_psvmcred["user_name"]
            password = host_psvmcred["password"]
        except KeyError:
            raise exc.HTTPBadRequest()
        try:
            utils.check_string_length(user_name, "Psvmcred user_name", 1, 255)
        except exception.InvalidInput as e:
            raise exc.HTTPBadRequest(explanation=e.format_message())

        try:
            psvmcred = self.api.create_psvmcred(context, user_name, password)
        except Exception:
            LOG.exception(_('Hit an exception'))
            raise

        return self._marshall_psvmcred(psvmcred)

    def show(self, req, id):
        """Shows the details of a psvmcred."""
        context = _get_context(req)
        AUTHORIZE(context, action='show')
        try:
            psvmcred = self.api.get_psvmcred(context, id)
        except exception.PSVMSwitchCredNotFound:
            LOG.info(_("Cannot show psvmcred cred: %s"), id)
            raise exc.HTTPNotFound()
        return self._marshall_psvmcred(psvmcred)

    def update(self, req, id, body):
        """Updates the user_name and/or password of given psvmcred."""
        context = _get_context(req)
        AUTHORIZE(context, action='update')

        if len(body) != 1:
            raise exc.HTTPBadRequest()
        try:
            updates = body["psvmcred"]
        except KeyError:
            raise exc.HTTPBadRequest()

        if len(updates) < 1:
            raise exc.HTTPBadRequest()

        for key in updates.keys():
            if key not in ["user_name", "password"]:
                raise exc.HTTPBadRequest()

        try:
            if 'user_name' in updates:
                utils.check_string_length(updates['user_name'],
                                          "Psvmcred user_name",
                                          1, 255)
            if 'password' in updates:
                utils.check_string_length(updates['password'],
                                          "Psvmcred password",
                                          1, 255)
        except exception.InvalidInput as e:
            raise exc.HTTPBadRequest(explanation=e.format_message())

        try:
            psvmcred = self.api.update_psvmcred(context, id, updates)
        except exception.PSVMSwitchCredNotFound:
            LOG.info(_('Cannot update psvmcred: %s'), id)
            raise exc.HTTPNotFound()

        return self._marshall_psvmcred(psvmcred)

    def delete(self, req, id):
        """Removes an psvmcred by id."""
        context = _get_context(req)
        AUTHORIZE(context, action='delete')
        try:
            self.api.delete_psvmcred(context, id)
        except exception.PSVMSwitchCredNotFound:
            LOG.info(_('Cannot delete psvmcred: %s'), id)
            raise exc.HTTPNotFound()

    def _marshall_psvmcred(self, psvmcred):
        _psvmcred = {}
        for key, value in psvmcred.items():
            # NOTE(danms): The original API specified non-TZ-aware timestamps
            if isinstance(value, datetime.datetime):
                value = value.replace(tzinfo=None)
            _psvmcred[key] = value
        return {"psvmcred": _psvmcred}


class Psvmcred(extensions.ExtensionDescriptor):
    """Admin-only psvmcred administration."""

    name = "Psvmcred"
    alias = "os-psvmcred"
    namespace = "http://docs.openstack.org/compute/ext/psvmcred/api/v1.1"
    updated = "2012-01-12T00:00:00Z"

    def get_resources(self):
        resources = []
        res = extensions.ResourceExtension(
            'os-psvmcred',
            PsvmcredController(),
            member_actions={"action": "POST", })
        resources.append(res)
        return resources
