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

"""Tests for the psvmcred api."""

from nova.api.openstack.compute.contrib import psvmcred
from nova import context
from nova import test
from nova.tests.api.openstack import fakes

PSVMCRED_LIST = [
        {"id": "1", "user_name": "user1", "password": "password1"},
        {"id": "2", "user_name": "user2", "password": "password2"},
        {"id": "3", "user_name": "user3", "password": "password3"},
        {"id": "4", "user_name": "user1", "password": "password4"}]
PSVMCRED = {"name": "psvmcred",
        "id": "1",
        "user_name": "userABC",
        "password": "passwordABC"}


class FakeRequest(object):
    environ = {"nova.context": context.get_admin_context()}


class PsvmcredTestCase(test.TestCase):
    """Test Case for psvmcred admin api."""

    def setUp(self):
        super(PsvmcredTestCase, self).setUp()
        self.controller = psvmcred.PsvmcredController()
        self.req = FakeRequest()
        self.user_req = fakes.HTTPRequest.blank('/v2/os-psvmcred')
        self.context = self.req.environ['nova.context']

    def test_index(self):
        def stub_list_psvmcred(context):
            if context is None:
                raise Exception()
            return PSVMCRED_LIST
        self.stubs.Set(self.controller.api, 'get_psvmcred_list',
                       stub_list_psvmcred)

        result = self.controller.index(self.req)

        self.assertEqual(PSVMCRED_LIST, result["psvmcreds"])

    def test_create(self):
        def stub_create_psvmcred(context, name, password):
            self.assertEqual(context, self.context, "context")
            self.assertEqual("userABC", name, "user_name")
            self.assertEqual("passwordABC", password, "password")
            return PSVMCRED
        self.stubs.Set(self.controller.api, "create_psvmcred",
                       stub_create_psvmcred)

        result = self.controller.create(self.req, {"psvmcred":
                                          {"user_name": "userABC",
                                           "password": "passwordABC"}})
        self.assertEqual(PSVMCRED, result["psvmcred"])

    def test_show(self):
        def stub_get_psvmcred(context, id):
            self.assertEqual(context, self.context, "context")
            self.assertEqual("1", id, "id")
            return PSVMCRED
        self.stubs.Set(self.controller.api, 'get_psvmcred',
                       stub_get_psvmcred)

        psvmcred = self.controller.show(self.req, "1")

        self.assertEqual(PSVMCRED, psvmcred["psvmcred"])

    def test_update(self):
        body = {"psvmcred": {"user_name": "new_name",
                              "password": "new_password"}}

        def stub_update_psvmcred(context, psvmcred, values):
            self.assertEqual(context, self.context, "context")
            self.assertEqual("1", psvmcred, "psvmcred")
            self.assertEqual(body["psvmcred"], values, "values")
            return PSVMCRED
        self.stubs.Set(self.controller.api, "update_psvmcred",
                       stub_update_psvmcred)

        result = self.controller.update(self.req, "1", body=body)

        self.assertEqual(PSVMCRED, result["psvmcred"])

    def test_delete(self):
        def stub_delete_psvmcred(context, psvmcred):
            self.assertEqual(context, self.context, "context")
            self.assertEqual("1", psvmcred, "psvmcred")
            stub_delete_psvmcred.called = True
        self.stubs.Set(self.controller.api, "delete_psvmcred",
                       stub_delete_psvmcred)

        self.controller.delete(self.req, "1")
        self.assertTrue(stub_delete_psvmcred.called)
