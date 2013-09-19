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

"""Tests for the psvm api."""

from nova.api.openstack.compute.contrib import psvm
from nova import context
from nova import test
from nova.tests.api.openstack import fakes

PSVM_LIST = [
        {"id": "1", "ip": "1.1.1.1", "switch_cred_id": "1"},
        {"id": "2", "ip": "1.1.1.2", "switch_cred_id": "2"},
        {"id": "3", "ip": "1.1.1.3", "switch_cred_id": "3"},
        {"id": "4", "ip": "1.1.1.4", "switch_cred_id": "4"}]
PSVM = {"name": "psvm",
        "id": "1",
        "ip": "1.2.3.4",
        "switch_cred_id": "5"}


class FakeRequest(object):
    environ = {"nova.context": context.get_admin_context()}


class PsvmTestCase(test.TestCase):
    """Test Case for psvm admin api."""

    def setUp(self):
        super(PsvmTestCase, self).setUp()
        self.controller = psvm.PsvmController()
        self.req = FakeRequest()
        self.user_req = fakes.HTTPRequest.blank('/v2/os-psvm')
        self.context = self.req.environ['nova.context']

    def test_index(self):
        def stub_list_psvm(context):
            if context is None:
                raise Exception()
            return PSVM_LIST
        self.stubs.Set(self.controller.api, 'get_psvm_list',
                       stub_list_psvm)

        result = self.controller.index(self.req)

        self.assertEqual(PSVM_LIST, result["psvms"])

    def test_create(self):
        def stub_create_psvm(context, ip, switch_cred_id):
            self.assertEqual(context, self.context, "context")
            self.assertEqual("1.2.3.4", ip, "ip")
            self.assertEqual("3", switch_cred_id, "switch_cred_id")
            return PSVM
        self.stubs.Set(self.controller.api, "create_psvm",
                       stub_create_psvm)

        result = self.controller.create(self.req, {"psvm":
                                          {"ip": "1.2.3.4",
                                           "switch_cred_id": "3"}})
        self.assertEqual(PSVM, result["psvm"])

    def test_show(self):
        def stub_get_psvm(context, id):
            self.assertEqual(context, self.context, "context")
            self.assertEqual("1", id, "id")
            return PSVM
        self.stubs.Set(self.controller.api, 'get_psvm',
                       stub_get_psvm)

        psvm = self.controller.show(self.req, "1")

        self.assertEqual(PSVM, psvm["psvm"])

    def test_update(self):
        body = {"psvm": {"ip": "4.3.2.1",
                              "switch_cred_id": "2"}}

        def stub_update_psvm(context, psvm, values):
            self.assertEqual(context, self.context, "context")
            self.assertEqual("1", psvm, "psvm")
            self.assertEqual(body["psvm"], values, "values")
            return PSVM
        self.stubs.Set(self.controller.api, "update_psvm",
                       stub_update_psvm)

        result = self.controller.update(self.req, "1", body=body)

        self.assertEqual(PSVM, result["psvm"])

    def test_delete(self):
        def stub_delete_psvm(context, psvm):
            self.assertEqual(context, self.context, "context")
            self.assertEqual("1", psvm, "psvm")
            stub_delete_psvm.called = True
        self.stubs.Set(self.controller.api, "delete_psvm",
                       stub_delete_psvm)

        self.controller.delete(self.req, "1")
        self.assertTrue(stub_delete_psvm.called)
