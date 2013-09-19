# Copyright 2012 OpenStack LLC.
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
#
#    ONOP psvm@onop.org

from sqlalchemy import Boolean, Column, DateTime, ForeignKey
from sqlalchemy import Integer, MetaData, String, Table

from nova.openstack.common.gettextutils import _
from nova.openstack.common import log as logging

LOG = logging.getLogger(__name__)


def _create_shadow_tables(migrate_engine, tables):
    meta = MetaData(migrate_engine)
    meta.bind = migrate_engine

    for table in tables:

        columns = []
        for column in table.columns:
            column_copy = None
            column_copy = column.copy()
            columns.append(column_copy)

        shadow_table_name = 'shadow_' + table.name
        shadow_table = Table(shadow_table_name, meta, *columns,
                             mysql_engine='InnoDB')
        try:
            shadow_table.create()
        except Exception as e:
            LOG.exception(_('Exception while creating table. %s') % e)


def upgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine

    psvm_switch_credential = Table('psvm_switch_credential', meta,
        Column('created_at', DateTime),
        Column('updated_at', DateTime),
        Column('deleted_at', DateTime),
        Column('deleted', Boolean),
        Column('id', Integer, primary_key=True, nullable=False,
               autoincrement=True),
        Column('user_name', String(length=255), nullable=False),
        Column('password', String(length=255), nullable=False),
        mysql_engine='InnoDB',
    )

    psvm_switch = Table('psvm_switch', meta,
        Column('created_at', DateTime),
        Column('updated_at', DateTime),
        Column('deleted_at', DateTime),
        Column('deleted', Boolean),
        Column('id', Integer, primary_key=True, nullable=False,
               autoincrement=True),
        Column('ip', String(length=255), nullable=False, unique=True),
        Column('num_connections', Integer, nullable=False, default=0),
        Column('switch_cred_id', Integer,
               ForeignKey('psvm_switch_credential.id'), nullable=False),
        mysql_engine='InnoDB',
    )

    psvm_switchport_binding = Table('psvm_switchport_binding', meta,
        Column('created_at', DateTime),
        Column('updated_at', DateTime),
        Column('deleted_at', DateTime),
        Column('deleted', Boolean),
        Column('id', Integer, primary_key=True, nullable=False,
               autoincrement=True),
        Column('switch_id', Integer, ForeignKey('psvm_switch.id'),
               nullable=False),
        Column('compute_node_id', Integer, nullable=False),
        Column('switch_port', String(length=255), nullable=False),
        mysql_engine='InnoDB',
    )

    tables = [psvm_switch_credential, psvm_switch,
              psvm_switchport_binding]

    for table in tables:
        try:
            table.create()
        except Exception as e:
            LOG.exception(_('Exception while creating table. %s') % e)

    _create_shadow_tables(migrate_engine, tables)


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine
    tables = []

    try:
        psvm_switchport_binding = Table('psvm_switchport_binding', meta,
                                        autoload=True)
        tables.append(psvm_switchport_binding)
    except Exception as e:
        LOG.exception(e)
    try:
        psvm_switch = Table('psvm_switch', meta, autoload=True)
        tables.append(psvm_switch)
    except Exception as e:
        LOG.exception(e)
    try:
        psvm_switch_credential = Table('psvm_switch_credential', meta,
                                       autoload=True)
        tables.append(psvm_switch_credential)
    except Exception as e:
        LOG.exception(e)
    try:
        shadow_psvm_switchport_binding = Table(
            'shadow_psvm_switchport_binding', meta, autoload=True)
        tables.append(shadow_psvm_switchport_binding)
    except Exception as e:
        LOG.exception(e)
    try:
        shadow_psvm_switch = Table('shadow_psvm_switch', meta, autoload=True)
        tables.append(shadow_psvm_switch)
    except Exception as e:
        LOG.exception(e)
    try:
        shadow_psvm_switch_credential = Table('shadow_psvm_switch_credential',
                                              meta, autoload=True)
        tables.append(shadow_psvm_switch_credential)
    except Exception as e:
        LOG.exception(e)

    for table in tables:
        try:
            table.drop()
        except Exception as e:
            LOG.exception(_('Exception while dropping table. %s') % e)
