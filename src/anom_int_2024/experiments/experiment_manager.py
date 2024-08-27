"""
Copyright (c) 2024 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
The Experiment Manager is responsible for managing new session requests,
running the experiments in threaded mode, storing the generated data, and
presenting the star-rated feedback. For more information in data-related tasks,
see the EXP_MGR_DB class.

It offers functionality for listing all available experiment types and includes
an auto-selection feature for session types. These functionalities are
respectively implemented by the functions mgr_exps_available() and
mgr_part_sess_type_auto().

The distinction between participant and sham sessions lies in the following
aspects:
- The construction of the exp_init_data dictionary differs in the
  exp_start_part(), exp_start_sham() functions.
- Both session types commence with the exp_start() function, executing identical
  code throughout the experimental phase.
- In the finalization process, participant sessions display the star-rated
  feedback, while sham sessions do not, as elucidated in the exp_finished()
  function.
"""

import inspect, traceback, time
from concurrent.futures import ThreadPoolExecutor
import tkinter as tk
import tkinter.messagebox as tkm

import numpy as np

import anom_int_2024
from anom_int_2024.experiments import EXP_MGR_DB, EXP_BASE
from anom_int_2024.experiments import WIN_FEEDB_STAR, WIN_SESSION, WIN_FEEDB_CIRCLE
from anom_int_2024.analysis import calc_star_feedback


# EXP_MGR

class EXP_MGR:

    def __init__(self, parent, db_local_filename):
        # Variables
        self.name = 'EXP_MGR'
        self.parent = parent                # RAVA_APP
        self.lg = self.parent.lg            # LOG
        self.cfg = self.parent.cfg          # CFG
        self.rng = self.parent.rng          # RNG

        # Debug
        self.lg.debug('{}: Initializing'.format(self.name))

        # Database
        self.db = EXP_MGR_DB(parent, db_local_filename)

        # Experiments
        self.th_exp = ThreadPoolExecutor(max_workers=1)
        self.future_exp_result = None
        self.exp = None
        self.exp_canceled = False

        # Callback functions
        self.cbkfcn_exp_finished = lambda: None

        # Windows
        self.win_session = WIN_SESSION(parent, self)
        self.win_feedb_star = WIN_FEEDB_STAR(parent)
        self.win_feedb_circle = WIN_FEEDB_CIRCLE(parent)


    def close(self):
        self.db.close()


    ## MGR

    def mgr_delay(self, delay_s):
        t0 = time.perf_counter()

        if self.exp is None:
            return

        while True:
            if time.perf_counter() - t0 >= delay_s:
                break

            if self.exp_canceled:
                break # Exits if exp is canceled

            var = tk.IntVar()
            self.parent.after(100, var.set, 1)
            self.parent.wait_variable(var)


    def mgr_exps_available(self):
        # Finds all classes in anomalous_interactions_2024.experiments which inherit from EXP_BASE
        session_type_data = []
        for name, cls in anom_int_2024.experiments.__dict__.items():
            if inspect.isclass(cls) and issubclass(cls, EXP_BASE) and cls is not EXP_BASE:
                session_type_data.append((name, cls))

        return dict(session_type_data)


    def mgr_part_sess_type_auto(self, sess_group, part_id):
        # Get all session types
        types_n, sess_types = self.db.groups_get_sess_types(sess_group)

        # Find available session types; DB side
        db_n_available_sess_type , db_available_sess_type = self.db.sess_get_part_available_sess_type(sess_group)

        # Retrieve part previous contributions
        part_prev_n, _, _, part_prev_sess_type = self.db.sess_get_part_contribution(sess_group, part_id)

        # Find available session type; Part side
        block_part_prev_sess_type = part_prev_sess_type[-1: -(part_prev_n % types_n + 1): -1] # Considers blocks of types_n sessions
        part_available_sess_type = set(sess_types).difference(block_part_prev_sess_type)

        # Intersection between db and part
        intersect_available_sess_type = db_available_sess_type.intersection(part_available_sess_type)
        intersect_n_available_sess_type = len(intersect_available_sess_type)

        # Priorize db side; Participant may contribute non-uniformly to the sess_types
        if intersect_n_available_sess_type == 0:
            final_available_sess_type = db_available_sess_type
            final_n_available_sess_type = db_n_available_sess_type
        else:
            final_available_sess_type = intersect_available_sess_type
            final_n_available_sess_type = intersect_n_available_sess_type

        # Randomly pick a sess_type using RAVA device
        if final_n_available_sess_type > 1:
            idx = self.rng.get_rng_int8s(n_ints=1, int_delta=final_n_available_sess_type-1, output_type='list')[0]
        else:
            idx = 0

        sess_type = list(final_available_sess_type)[idx]
        return sess_type


    ## EXP

    def exp_start_part(self, part_id, part_name, sess_group, sess_type):
        # Is there any missing sham session?
        sham_n_missing, _ = self.db.sess_get_sham_missing(sess_group)
        if sham_n_missing:
            tkm.showerror(parent=self.parent, title='Error',
                          message='Please collect the missing sham session before starting a new participant session!')
            return

        ## Get sess_type
        sess_n_per_type = self.db.groups_get(sess_group, res_type='dol')['sess_n_per_type'][0]

        # Find available session types; DB side
        db_n_available_sess_type , db_available_sess_type = self.db.sess_get_part_available_sess_type(sess_group)

        if db_n_available_sess_type == 0:
            tkm.showinfo(parent=self.parent, title='Group finished',
                         message='All {} sessions for each exp type have already been conducted in group {}'\
                                 .format(sess_n_per_type, sess_group))
            return

        # Manually assign sess_type
        if sess_type != 'Auto':

            # Test if given sess_type is still available
            if len(db_available_sess_type.intersection({sess_type})) == 0:
                tkm.showinfo(parent=self.parent, title='Group finished',
                             message='All {} sessions for exp type = {} have already been conducted in group {}'\
                                     .format(sess_n_per_type, sess_type, sess_group))
                return

        # Auto assign sess_type
        else:
            sess_type = self.mgr_part_sess_type_auto(sess_group, part_id)

        ## Initial data
        exp_init_data = {'part_id': part_id,
                         'part_name': part_name,
                         'sess_group': sess_group,
                         'sess_type': sess_type,
                         'sess_sham': False,
                         'part_hash_pointer': None,
                         'feedb_rng_target': None       # Randomly selected at sessions' start
                         }

        # Start experiment
        self.exp_start(exp_init_data, self.rng, self.win_feedb_circle)


    def exp_start_sham(self, sess_group):
        # Get part_hash_pointer
        n_missing, part_hashes = self.db.sess_get_sham_missing(sess_group)

        if n_missing == 0:
            tkm.showinfo(parent=self.parent, title='Info',
                         message='There are no missing Control sessions in group {}'.format(sess_group))
            return

        part_hash_pointer = part_hashes[-1] # Last session

        # Get parameters from the associated part session
        sess_type, feedb_rng_target = self.db.sess_get_part_initial_pars(part_hash_pointer)

        # Initial data
        exp_init_data = {'part_id': 0,
                         'part_name': '',
                         'sess_group': sess_group,
                         'sess_type': sess_type,                            # Inherits the associated part session value
                         'sess_sham': True,
                         'part_hash_pointer': part_hash_pointer,
                         'feedb_rng_target': feedb_rng_target               # Inherits the associated part session value
                         }

        # Start experiment
        self.exp_start(exp_init_data, self.rng, self.win_feedb_circle)


    def exp_start(self, exp_init_data, rng, win_feedb):
        # Create exp instance
        exp_dict = self.mgr_exps_available()
        sess_type = exp_init_data['sess_type']
        self.exp = exp_dict[sess_type](rng, win_feedb)
        self.exp_canceled = False

        # Simulation Parameters
        sess_i = exp_init_data['simulation_sess_i'] if 'simulation_sess_i' in exp_init_data else 0
        sess_n = exp_init_data['simulation_sess_n'] if 'simulation_sess_n' in exp_init_data else 1
        simulation_delay_min = exp_init_data['simulation_delay_min'] if 'simulation_delay_min' in exp_init_data else 0

        # Fast Simulation?
        simulation_fast = exp_init_data['simulation_fast'] if 'simulation_fast' in exp_init_data else False

        if simulation_fast:
            # Do not show win_session and not perform the countdowns before starting the session
            pass

        else:
            # Show Window session
            self.win_session.show(sess_i, sess_n)

            # Window session - Delay (Used in standard simulation)
            if simulation_delay_min:
                self.win_session.countdown(self.win_session.text_delay, simulation_delay_min)
                self.mgr_delay(simulation_delay_min * 60)

            # Window session - Prepare
            prepare_dur_min = self.exp.cfg['prepare_dur_min']
            if prepare_dur_min:
                self.win_session.countdown(self.win_session.text_prepare, prepare_dur_min)
                self.mgr_delay(int(prepare_dur_min * 60))

            # Exp canceled during preparation?
            if self.exp_canceled:
                return

            # Window session - Disable cancel button
            self.win_session.bt_cancel.state(['disabled'])

            # Window session - Intention
            self.win_session.countdown(self.win_session.text_intention, self.exp.cfg['sess_dur_min'])

            # Window session - Freeze intention instruction for instruction_dur_sec
            instruction_dur_sec = self.exp.cfg['instruction_dur_sec']
            if instruction_dur_sec:
                self.mgr_delay(instruction_dur_sec)

        # Run experiment
        self.future_exp_result = self.th_exp.submit(self.exp.run, exp_init_data)

        # Set finished callback
        self.future_exp_result.add_done_callback(self.exp_finished)


    def exp_cancel(self):
        # It is only possible to cancel the experiment during the preparation epoch
        self.exp_canceled = True


    def exp_finished(self, future):
        # Raised any exception?
        exc = future.exception()
        if exc is not None:
            exc_traceback = traceback.print_exc()
            self.lg.error('{}: Experiment error -- {}\n{}'.format(self.name, exc, exc_traceback))
            return

        # Get result
        exp_data, exp_init_data = future.result()
        sess_sham = exp_init_data['sess_sham']

        # Participant sess: Calculate star feedback
        if not sess_sham:
            # Analyze target bytes
            n_stars = calc_star_feedback(exp_data)

            # Save star result
            exp_data['feedb_stars'] = n_stars

        # Fast Simulation?
        simulation_fast = exp_init_data['simulation_fast'] if 'simulation_fast' in exp_init_data else False

        if not simulation_fast:
            # Window session - Enable cancel button and close
            self.win_session.bt_cancel.state(['!disabled'])
            self.win_session.hide()

            # Participant sess: Show star feedback
            if not sess_sham:
                self.win_feedb_star.show(n_stars)

        # Save data
        self.exp_save(exp_data)

        # Callback function
        self.cbkfcn_exp_finished(exp_data)


    def exp_save(self, exp_data):
        # Local
        sess_hash = self.db.local_write(self.db.table_sessions, exp_data)
        self.lg.info('{}: Exp session saved to local DB, hash={}'.format(self.name, sess_hash))

        return sess_hash


    def cbkreg_exp_finished(self, fcn_exp_finished):
        if callable(fcn_exp_finished):
            self.cbkfcn_exp_finished = fcn_exp_finished
            self.lg.debug('{} Callback: Registering Exp Finished function to {}'.format(self.name, fcn_exp_finished.__name__))

        elif fcn_exp_finished is None:
            self.cbkfcn_exp_finished = lambda: None
            self.lg.debug('{} Callback: Unregistering Exp Finished function'.format(self.name))

        else:
            self.lg.error('{} Callback: Provide fcn_exp_finished as a function or None'.format(self.name))