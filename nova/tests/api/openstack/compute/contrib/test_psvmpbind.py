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

"""Tests for the psvmpbind api."""

from nova.api.openstack.compute.contrib import psvmpbind
from nova import context
from nova import test
from nova.tests.api.openstack import fakes

PSVMPBIND_LIST = [
        {"id": "1", "switch_id": "1",
            "compute_node_id": "1", "switch_port": "sp-1-1"},
        {"id": "2", "switch_id": "2",
            "compute_node_id": "2", "switch_port": "sp-1-2"},
        {"id": "3", "switch_id": "2",
            "compute_node_id": "3", "switch_port": "sp-2-1"},
        {"id": "4", "switch_id": "2",
            "compute_node_id": "4", "switch_port": "sp-2-1"}]
PSVMPBIND = {"name": "psvmpbind",
        "id": "1",
        "switch_id": "1",
        "compute_node_id": "1",
        "switch_port": "sp-1-1"}


class FakeRequest(object):
    environ = {"nova.context": context.get_admin_context()}


class PsvmpbindTestCase(test.TestCase):
    """Test Case for psvmpbind admin api."""

    def setUp(self):
        super(PsvmpbindTestCase, self).setUp()
        self.controller = psvmpbind.PsvmpbindController()
        self.req = FakeRequest()
        self.user_req = fakes.HTTPRequest.blank('/v2/os-psvmpbind')
        self.context = self.req.environ['nova.context']

    def test_index(self):
        def stub_list_psvmpbind(context):
            if context is None:
                raise Exception()
            return PSVMPBIND_LIST
        self.stubs.Set(self.controller.api, 'get_psvmpbind_list',
                       stub_list_psvmpbind)

        result = self.controller.index(self.req)

        self.assertEqual(PSVMPBIND_LIST, result["psvmpbinds"])

    def test_create(self):
        def stub_create_psvmpbind(context, switch_id, compute_node_id,
                switch_port):
            self.assertEqual(context, self.context, "context")
            self.assertEqual("1", switch_id, "switch_id")
            self.assertEqual("1", compute_node_id, "compute_node_id")
            self.assertEqual("sp-1-1", switch_port, "switch_port")
            return PSVMPBIND
        self.stubs.Set(self.controller.api, "create_psvmpbind",
                       stub_create_psvmpbind)

        result = self.controller.create(self.req, {"psvmpbind":
                                          {"switch_id": "1",
                                           "compute_node_id": "1",
                                           "switch_port": "sp-1-1"}})
        self.assertEqual(PSVMPBIND, result["psvmpbind"])

    def test_show(self):
        def stub_get_psvmpbind(context, id):
            self.assertEqual(context, self.context, "context")
            self.assertEqual("1", id, "id")
            return PSVMPBIND
        self.stubs.Set(self.controller.api, 'get_psvmpbind',
                       stub_get_psvmpbind)

        psvmpbind = self.controller.show(self.req, "1")

        self.assertEqual(PSVMPBIND, psvmpbind["psvmpbind"])

    def test_update(self):
        body = {"psvmpbind": {"switch_id": "5",
                              "compute_node_id": "5",
                              "switch_port": "port-5-5",
                              }}

        def stub_update_psvmpbind(context, psvmpbind, values):
            self.assertEqual(context, self.context, "context")
            self.assertEqual("1", psvmpbind, "psvmpbind")
            self.assertEqual(body["psvmpbind"], values, "values")
            return PSVMPBIND
        self.stubs.Set(self.controller.api, "update_psvmpbind",
                       stub_update_psvmpbind)

        result = self.controller.update(self.req, "1", body=body)

        self.assertEqual(PSVMPBIND, result["psvmpbind"])

    def test_delete(self):
        def stub_delete_psvmpbind(context, psvmpbind):
            self.assertEqual(context, self.context, "context")
            self.assertEqual("1", psvmpbind, "psvmpbind")
            stub_delete_psvmpbind.called = True
        self.stubs.Set(self.controller.api, "delete_psvmpbind",
                       stub_delete_psvmpbind)

        self.controller.delete(self.req, "1")
        self.assertTrue(stub_delete_psvmpbind.called)
