"""
Copyright (c) 2024 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
This module implements the Database functionality within the Experiment Manager.
It facilitates access to local SQLite databases, coordinated by the sqlalchemy
toolkit.

The sessions data is organized into two distinct databases: groups and sessions,
with their definitions outlined in the exp_parameters.py file.

Within this module, low-level functions are defined to handle essential
operations such as connecting, reading, writing, and deleting entries in the
databases. Additionally, higher-level methods are provided for extracting
specific information.
"""

import os.path

from sqlalchemy import create_engine, inspect, select, insert, delete, asc, MetaData

from anom_int_2024.experiments import table_groups, table_sessions


# EXP_MGR_DB

class EXP_MGR_DB:

    def __init__(self, parent, db_local_filename):
        # Variables
        self.name = 'EXP_MGR_DB'
        self.parent = parent                # RAVA_SUBAPP_EXPERIMENTS
        self.lg = self.parent.lg            # LOG
        self.cfg = self.parent.cfg          # CFG

        # Debug
        self.lg.debug('{}: Initializing'.format(self.name))

        # Local DB
        self.local_eng = None
        self.local_meta = None
        self.table_groups = None
        self.table_sessions = None
        self.local_connect(db_local_filename) # Defines previous variables


    def close(self):
        self.local_meta.clear()
        self.local_eng.dispose()


    ## DB local

    def local_connect(self, local_filename):
        # Parameters
        local_path, local_basename = os.path.split(local_filename)

        # Path exists? If not create
        if not os.path.exists(local_path):
            self.lg.info('{}: Creating storage path {}'.format(self.name, local_path))
            os.makedirs(local_path)

        # DB objects
        self.lg.info('{}: Connecting to local DB {}'.format(self.name, local_basename))

        self.local_eng = create_engine('sqlite:///{}'.format(local_filename))
        self.local_meta = MetaData()

        # Groups table
        self.table_groups = table_groups(self.local_meta)

        if inspect(self.local_eng).has_table('groups'):
            self.lg.debug('{}: Loading groups Table'.format(self.name))

        else:
            self.lg.info('{}: Creating groups Table'.format(self.name))
            self.local_meta.create_all(self.local_eng)

        # Sessions table
        self.table_sessions = table_sessions(self.local_meta)

        if inspect(self.local_eng).has_table('sessions'):
            self.lg.debug('{}: Loading sessions Table'.format(self.name))
        else:
            self.lg.info('{}: Creating sessions Table'.format(self.name))
            self.local_meta.create_all(self.local_eng)


    def local_read(self, table, fields=[], where=[], res_type='tuple', order_by_date=True):
        # SQL Command
        if len(fields) == 0 and len(where) == 0:
            comm = select(table)
        elif len(fields) == 0:
            comm = select(table).where(*where)
        else:
            comm = select(table.c[*fields]).where(*where)

        if table == self.table_sessions and order_by_date:
            comm = comm.order_by(asc(table.c.dt_start))

        # Read Data
        try:
            with self.local_eng.connect() as conn:
                read_res = conn.execute(comm)
            cursor = read_res.cursor
            if len(fields) == 1:
                res = read_res.scalars().all()
            else:
                res = read_res.all()
            res_n = len(res)

        except Exception as err:
            self.lg.error('{}: Error reading local DB, table {} - {}'.format(self.name, table.name, err))
            return None, []

        ## Result type
        # list of dicts
        if res_type == 'lod':
            col_names = [col[0] for col in cursor.description]
            res = [dict(zip(col_names, r)) for r in res]
        # dict of lists
        elif res_type == 'dol':
            col_names = [col[0] for col in cursor.description]
            vals = [[x[i] for x in res] for i in range(len(col_names))]
            res = dict(zip(col_names, vals))

        # Debug
        self.lg.debug('{}: Reading local DB, table {}, returning {} entries'.format(self.name, table.name, res_n))

        return res_n, res


    def local_write(self, table, values_dict={}):
        # Test input
        if len(values_dict) == 0:
            return None

        # SQL Command
        comm = insert(table).values(**values_dict)

        # Write Data
        try:
            with self.local_eng.begin() as conn:
                res = conn.execute(comm)
                primary_key = res.inserted_primary_key[0]

        except Exception as err:
            self.lg.error('{}: Error writing to local DB, table {} - {}'.format(self.name, table.name, err))
            return None

        # Debug
        self.lg.debug('{}: Writing to local DB, table {}, creating pk {}'.format(self.name, table.name, primary_key))

        return primary_key


    def local_delete(self, table, where=[]):
        # Test input
        if len(where) == 0:
            return 0

        # SQL Command
        comm = delete(table).where(*where)

        # Delete Data
        try:
            with self.local_eng.begin() as conn:
                res = conn.execute(comm)
            n_del = res.rowcount

        except Exception as err:
            self.lg.error('{}: Error deleting local DB data, table {} - {}'.format(self.name, table.name, err))
            return None

        # Debug
        self.lg.debug('{}: Deleting local DB data, table {}, erased {} entries'.format(self.name, table.name, n_del))

        return n_del


    ## DB high-level methods: Groups

    def groups_add(self, data_dict):
        # Group already exists?
        group = data_dict['group']

        if len(self.groups_get(group)):
            self.lg.error('{}: Can\'t add group {}. Group already exists'.format(self.name, group))

        # Add group
        else:
            self.lg.info('{}: Adding group {}'.format(self.name, group))
            self.local_write(self.table_groups, values_dict=data_dict)


    def groups_del(self, sess_group):
        self.lg.info('{}: Deleting group {}'.format(self.name, sess_group))
        self.local_delete(self.table_groups, where=[self.table_groups.c.group == sess_group])


    def groups_get(self, group=None, res_type='tuple'):
        where = [self.table_groups.c.group == group] if group is not None else []
        _, group_data = self.local_read(self.table_groups, where=where, res_type=res_type)
        return group_data


    def groups_get_sess_types(self, group):
        _, group_data = self.local_read(self.table_groups, fields = ['sess_types'],
                                     where = [self.table_groups.c.group == group],
                                     res_type='tuple')
        if len(group_data):
            sess_types = group_data[0].split(',')
        else:
            sess_types = []

        return len(sess_types), sess_types


    ## DB high-level methods: Sessions

    def sess_get_data(self, sess_hash):
        _, sess_data = self.local_read(self.table_sessions, fields=[], res_type='lod',
                                            where=[self.table_sessions.c.sess_hash == sess_hash])
        res = sess_data[0] if len(sess_data) else None
        return res


    def sess_get_part_n_remaining(self, sess_group):
        # Get total number of sessions
        sess_type_n, _ = self.groups_get_sess_types(sess_group)
        if sess_type_n == 0:
            return None

        sess_n_per_type = self.groups_get(sess_group, res_type='dol')['sess_n_per_type'][0]
        sess_n = sess_type_n * sess_n_per_type

        # Get current number of sessions
        sess_n_current, _ = self.local_read(self.table_sessions, fields=['sess_hash'],
                                            where=[self.table_sessions.c.sess_group == sess_group,
                                                   self.table_sessions.c.sess_sham == False])

        sess_n_remaining =  sess_n - sess_n_current
        return sess_n_remaining


    def sess_get_part_available_sess_type(self, sess_group):
        # Get group info
        _, group_sess_types = self.groups_get_sess_types(sess_group)
        sess_n_per_type = self.groups_get(sess_group, res_type='dol')['sess_n_per_type'][0]

        # Get current sess_types
        _, part_sess_types = self.local_read(self.table_sessions, fields=['sess_type'],
                                           where=[self.table_sessions.c.sess_group == sess_group,
                                                  self.table_sessions.c.sess_sham == False])

        available_sess_type = set()
        for sess_type in group_sess_types:
            if part_sess_types.count(sess_type) < sess_n_per_type:
                available_sess_type.add(sess_type)

        return len(available_sess_type), available_sess_type


    def sess_get_part_contribution(self, sess_group, part_id):
        fields = ['dt_start', 'part_name', 'sess_type']
        part_n, part_data = self.local_read(self.table_sessions, fields=fields, res_type='dol',
                                            where=[self.table_sessions.c.part_id == part_id,
                                                   self.table_sessions.c.sess_group == sess_group,
                                                   self.table_sessions.c.sess_sham == False])
        dt_start = [str(dt)[:16] for dt in part_data['dt_start']]
        part_name = part_data['part_name']
        sess_type = part_data['sess_type']

        return part_n, dt_start, part_name, sess_type


    def sess_get_part_sessions(self, sess_group=None, part_id=None, res_type='tuple'):
        fields = ['sess_hash', 'dt_start', 'sess_group', 'part_id', 'feedb_stars']

        # Define filters
        filters = [self.table_sessions.c.sess_sham == False]

        if sess_group is not None:
            filters += [self.table_sessions.c.sess_group == sess_group]
        if part_id is not None:
            filters += [self.table_sessions.c.part_id == part_id]

        # Get data
        _, part_data = self.local_read(self.table_sessions, fields=fields, where=filters, res_type=res_type)

        return part_data


    def sess_get_part_initial_pars(self, sess_hash):
        fields = ['sess_type', 'feedb_rng_target']
        _, data = self.local_read(self.table_sessions, fields=fields, res_type='tuple',
                                            where=[self.table_sessions.c.sess_hash == sess_hash])

        sess_type, feedb_rng_target = data[0]
        return sess_type, feedb_rng_target


    def sess_get_sham_n(self, sess_group):
        # Get participant session hashes
        n, _ = self.local_read(self.table_sessions, fields=['sess_hash'],
                                            where=[self.table_sessions.c.sess_group == sess_group,
                                                   self.table_sessions.c.sess_sham == True])

        return n


    def sess_get_sham_missing(self, sess_group):
        # Get participant session hashes
        _, hash_part = self.local_read(self.table_sessions, fields=['sess_hash'],
                                            where=[self.table_sessions.c.sess_group == sess_group,
                                                   self.table_sessions.c.sess_sham == False])

        # Get control session pointers to part hashes
        _, hash_pointer_sham = self.local_read(self.table_sessions, fields=['part_hash_pointer'],
                                                    where=[self.table_sessions.c.sess_group == sess_group,
                                                           self.table_sessions.c.sess_sham == True])

        hash_missing = [h for h in hash_part if h not in hash_pointer_sham]
        return len(hash_missing), hash_missing