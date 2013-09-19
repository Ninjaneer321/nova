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


class Psvm(base.NovaPersistentObject, base.NovaObject):
    # Version 1.0: Initial version
    VERSION = '1.0'

    fields = {
        'id': fields.IntegerField(),
        'ip': fields.StringField(),
        'switch_cred_id': fields.IntegerField(),
        }

    @staticmethod
    def _from_db_object(context, switch, db_switch):
        for key in switch.fields:
            switch[key] = db_switch[key]
        switch._context = context
        switch.obj_reset_changes()
        return switch

    @base.remotable_classmethod
    def get_by_id(cls, context, switch_id):
        db_switch = db.switch_get(context, switch_id)
        return cls._from_db_object(context, cls(), db_switch)

    @base.remotable
    def create(self, context, ip, switch_cred_id):
        db_switch = db.switch_create(context,
                                     {'ip': ip,
                                      'switch_cred_id': switch_cred_id})
        return self._from_db_object(context, self, db_switch)

    @base.remotable
    def save(self, context):
        updates = self.obj_get_changes()

        payload = {'id': self.id}
        if 'ip' in updates:
            payload['ip'] = updates['ip']
        if 'switch_cred_id' in updates:
            payload['switch_cred_id'] = updates['switch_cred_id']
        updates.pop('id', None)
        db_switch = db.switch_update(context, self.id, updates)
        return self._from_db_object(context, self, db_switch)

    @base.remotable
    def destroy(self, context):
        db.switch_delete(context, self.id)


class PsvmList(base.ObjectListBase, base.NovaObject):
    # Version 1.0: Initial version
    VERSION = '1.0'

    fields = {
        'objects': fields.ListOfObjectsField('Psvm'),
        }
    child_versions = {
        '1.0': '1.0',
        }

    @base.remotable_classmethod
    def get_all(cls, context):
        db_switchs = db.switch_get_all(context)
        return base.obj_make_list(context, cls(context),
                                  Psvm, db_switchs)
