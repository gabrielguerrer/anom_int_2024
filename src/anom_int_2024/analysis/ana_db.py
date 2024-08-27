"""
Copyright (c) 2024 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
This module implements the database functionality within the Analysis Module,
enabling connections to a local SQLite database and facilitating data retrieval.
"""

import os.path

from sqlalchemy import create_engine, select, asc, MetaData

from anom_int_2024.experiments import table_sessions

# ANA_DB

class ANA_DB:

    def __init__(self):
        # Local DB
        self.local_eng = None
        self.local_meta = None
        self.table_sessions = None

    def close(self):
        self.local_meta.clear()
        self.local_eng.dispose()


    def connect(self, filename):
        # File exists?
        if not os.path.isfile(filename):
            return False

        # DB objects
        self.local_eng = create_engine('sqlite:///{}'.format(filename))
        self.local_meta = MetaData()

        # Sessions table
        self.table_sessions = table_sessions(self.local_meta)

        return True


    def read(self, fields=[], where=[], res_type='tuple', order_by_date=True):
        # SQL Command
        if len(fields) == 0 and len(where) == 0:
            comm = select(self.table_sessions)
        elif len(fields) == 0:
            comm = select(self.table_sessions).where(*where)
        else:
            comm = select(self.table_sessions.c[*fields]).where(*where)

        comm = comm.order_by(asc(self.table_sessions.c.dt_start))

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

        return res_n, res


    def sess_get_fields(self, fields, filter_sess_group, filter_sess_type, filter_sess_sham, filter_part_id, res_type='tuple'):
        filters = []

        if filter_sess_group is not None:
            filters += [self.table_sessions.c.sess_group == filter_sess_group]

        if filter_sess_type is not None:
            filters += [self.table_sessions.c.sess_type == filter_sess_type]

        if filter_sess_sham is not None:
            filters += [self.table_sessions.c.sess_sham == filter_sess_sham]

        if filter_part_id is not None:
            filters += [self.table_sessions.c.part_id == filter_part_id]

        return self.read(fields, where=filters, res_type=res_type, order_by_date=True)


    def sess_get_data(self, sess_hashes, res_type='lod'):
        filters = [self.table_sessions.c.sess_hash.in_(sess_hashes)]

        return self.read(where=filters, res_type=res_type, order_by_date=True)