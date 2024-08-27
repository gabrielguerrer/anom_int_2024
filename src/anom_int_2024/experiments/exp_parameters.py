"""
Copyright (c) 2024 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
This file defines all parameters used in the exp module. It encompasses database
definitions, experiment configurations, and star-indexed ratings linked to
session p-values.
"""

import os

from sqlalchemy import Table, Column, DateTime, SmallInteger, Integer, Float,Boolean, String, PickleType

from rng_rava import D_PWM_FREQ, D_RNG_POSTPROC


# FILES

FILES_PATH = os.path.join(os.path.expanduser('~'), '.rava/')

DB_LOCAL_FILENAME = os.path.join(FILES_PATH, 'anom_int_2024.db')
DB_SIM_LOCAL_FILENAME = os.path.join(FILES_PATH, 'anom_int_2024_sim.db')


# DB

def table_groups(meta):
   return Table('groups', meta,
               Column('group', Integer, primary_key=True, nullable=False),
               Column('sess_types', String),
               Column('sess_n_per_type', Integer),
               Column('type_auto', Boolean)
               )


def table_sessions( meta):
   return Table('sessions', meta,
               Column('sess_hash', String(), primary_key=True, nullable=False),
               Column('sess_group', SmallInteger),
               Column('sess_type', String),
               Column('sess_sham', Boolean),
               Column('part_hash_pointer', String(10)),
               Column('part_id', Integer),
               Column('part_name', String),
               Column('dt_start', DateTime),
               Column('t_total_s', Float),
               Column('frame_n', Integer),
               Column('frame_dur_ms', SmallInteger),
               Column('feedb_stars', SmallInteger),
               Column('feedb_rng_target', String(1)),
               Column('feedb_mag', PickleType),
               Column('feedb_mag_avg', PickleType),
               Column('rng_sn', String(8)),
               Column('rng_bytes_per_frame', SmallInteger),
               Column('rng_bytes_a', PickleType),
               Column('rng_bytes_b', PickleType),
               Column('rng_bytes_idx_a', PickleType),
               Column('rng_bytes_idx_b', PickleType)
               )


# EXPERIMENTS

EXP_CFG = {'rng_setup_pwm_freq': D_PWM_FREQ['50_KHZ'],
           'rng_setup_pwm_duty': 20,
           'rng_setup_si': 10,
           'rng_postproc_id': D_RNG_POSTPROC['NONE'],
           'rng_bytes_per_frame': 1,
           'sess_hash_n_bytes': 5,
           'sess_frame_dur_ms': 100,
           'sess_dur_min': 5,
           'feedb_n_avg': 30,
           'feedb_mag_min': 0.03,
           'instruction_dur_sec': 5,
           'prepare_dur_min': 3
           }

EXP_4_CFG = EXP_CFG.copy()
EXP_4_CFG['rng_bytes_per_frame'] = 2


# RESULTS

D_RES_P_TO_STARS = {1.00: 1,
                    0.30: 2,
                    0.05: 3
                    }

TXT_STAR_EXTRA = '\n\nAgradecemos sua colaboração\nAguarde, já retornaremos à videoconferência'
TXT_STAR_1 = 'Bom resultado!' + TXT_STAR_EXTRA
TXT_STAR_2 = 'Ótimo resultado!!' + TXT_STAR_EXTRA
TXT_STAR_3 = 'Excelente resultado!!!' + TXT_STAR_EXTRA


# INSTRUCTIONS

TXT_SESS_DELAY = 'Intervalo entre sessões\n \n '
TXT_SESS_PREPARE = 'Encontre uma posição confortável\nRespire lenta e profundamente\nLibere-se de qualquer preocupação'
TXT_SESS_INTENTION = 'Intencione o aumento do círculo\n \n '