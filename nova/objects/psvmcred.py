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
from nova import exception
from nova.objects import base
from nova.objects import fields


class Psvmcred(base.NovaPersistentObject, base.NovaObject):
    # Version 1.0: Initial version
    VERSION = '1.0'

    fields = {
        'id': fields.IntegerField(),
        'user_name': fields.StringField(),
        'password': fields.StringField(),
        }

    @staticmethod
    def _from_db_object(context, cred, db_cred):
        for key in cred.fields:
            cred[key] = db_cred[key]
        cred._context = context
        cred.obj_reset_changes()
        return cred

    def _assert_no_hosts(self, action):
        if 'hosts' in self.obj_what_changed():
            raise exception.ObjectActionError(
                action=action,
                reason='hosts updated inline')

    @base.remotable_classmethod
    def get_by_id(cls, context, cred_id):
        db_cred = db.switch_cred_get(context, cred_id)
        return cls._from_db_object(context, cls(), db_cred)

    @base.remotable
    def create(self, context, user_name, password):
        db_cred = db.switch_cred_create(context, {'user_name': user_name,
                                                  'password': password})
        return self._from_db_object(context, self, db_cred)

    @base.remotable
    def save(self, context):
        #self._assert_no_hosts('save')
        updates = self.obj_get_changes()

        payload = {'id': self.id}
        if 'user_name' in updates:
            payload['user_name'] = updates['user_name']
        if 'password' in updates:
            payload['password'] = updates['password']
        updates.pop('id', None)
        db_cred = db.switch_cred_update(context, self.id, updates)
        return self._from_db_object(context, self, db_cred)

    @base.remotable
    def destroy(self, context):
        db.switch_cred_delete(context, self.id)


class PsvmcredList(base.ObjectListBase, base.NovaObject):
    # Version 1.0: Initial version
    VERSION = '1.0'

    fields = {
        'objects': fields.ListOfObjectsField('Psvmcred'),
        }
    child_versions = {
        '1.0': '1.0',
        }

    @base.remotable_classmethod
    def get_all(cls, context):
        db_creds = db.switch_cred_get_all(context)
        return base.obj_make_list(context, cls(context),
                                  Psvmcred, db_creds)
