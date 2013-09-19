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

from nova import db
from nova.objects import base
from nova.objects import fields


class Psvmpbind(base.NovaPersistentObject, base.NovaObject):
    # Version 1.0: Initial version
    VERSION = '1.0'

    fields = {
        'id': fields.IntegerField(),
        'switch_id': fields.IntegerField(),
        'compute_node_id': fields.IntegerField(),
        'switch_port': fields.StringField(),
        }

    @staticmethod
    def _from_db_object(context, pbind, db_pbind):
        for key in pbind.fields:
            pbind[key] = db_pbind[key]
        pbind._context = context
        pbind.obj_reset_changes()
        return pbind

    @base.remotable_classmethod
    def get_by_id(cls, context, pbind_id):
        db_pbind = db.switchport_binding_get(context, pbind_id)
        return cls._from_db_object(context, cls(), db_pbind)

    @base.remotable
    def create(self, context,
               switch_id,
               compute_node_id,
               switch_port):
        db_pbind = db.switchport_binding_create(context,
                                                {'switch_id': switch_id,
                                                 'compute_node_id':
                                                 compute_node_id,
                                                 'switch_port': switch_port})
        return self._from_db_object(context, self, db_pbind)

    @base.remotable
    def save(self, context):
        updates = self.obj_get_changes()

        payload = {'id': self.id}
        if 'switch_id' in updates:
            payload['switch_id'] = updates['switch_id']
        if 'compute_node_id' in updates:
            payload['compute_node_id'] = updates['compute_node_id']
        if 'switch_port' in updates:
            payload['switch_port'] = updates['switch_port']

        updates.pop('id', None)
        db_pbind = db.switchport_binding_update(context, self.id, updates)
        return self._from_db_object(context, self, db_pbind)

    @base.remotable
    def destroy(self, context):
        db.switchport_binding_delete(context, self.id)


class PsvmpbindList(base.ObjectListBase, base.NovaObject):
    # Version 1.0: Initial version
    VERSION = '1.0'

    fields = {
        'objects': fields.ListOfObjectsField('Psvmpbind'),
        }
    child_versions = {
        '1.0': '1.0',
        }

    @base.remotable_classmethod
    def get_all(cls, context):
        db_pbinds = db.switchport_binding_get_all(context)
        return base.obj_make_list(context, cls(context),
                                  Psvmpbind, db_pbinds)

    @base.remotable_classmethod
    def get_by_host(cls, context, host):
        db_pbinds = db.switchport_bind_get_by_host(context, host)
        return base.obj_make_list(context, cls(context),
                                  Psvmpbind, db_pbinds)
