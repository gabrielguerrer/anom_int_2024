"""
Copyright (c) 2024 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
The fast simulation module allows for collecting numerous experimental sessions
using pregenerated files for randomness input. This is useful for detecting
potential systematic errors and validating statistical distributions against
expected chance outcomes.

To generate simulated sessions, first create an experimental group specifying
the desired experiment types and the number of sessions per type. Then, select
the experiment group in the fast simulation window and click 'Start'. All
sessions will be generated in one go.
"""

import os
import time

import numpy as np

import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as tkm

from rng_rava.tk import RAVA_SUBAPP
from anom_int_2024.experiments import EXP_CFG, EXP_4_CFG
from anom_int_2024.simulations import RNG_FROM_FILE, FEEDB_DUMMY


# PARAMETERS

PAD = 10

BYTES_EXP_1 = int(EXP_CFG['rng_bytes_per_frame'] * EXP_CFG['sess_dur_min'] * 60 / (EXP_CFG['sess_frame_dur_ms'] / 1000)) + 2
BYTES_EXP_2 = BYTES_EXP_1
BYTES_EXP_3 = BYTES_EXP_1 - 1
BYTES_EXP_4 = int((EXP_4_CFG['rng_bytes_per_frame'] + 1) * EXP_4_CFG['sess_dur_min'] * 60 / (EXP_4_CFG['sess_frame_dur_ms'] / 1000)) + 2


# RAVA_SUBAPP_SIMULATIONS_FAST

class RAVA_SUBAPP_SIMULATIONS_FAST(RAVA_SUBAPP):

    cfg_default_str = '''
    [SIM_FAST]
    files_bytes_a =
    files_bytes_b =
    '''


    def __init__(self, parent):

        # Initialize RAVA_SUBAPP
        name = 'RAVA_SUBAPP FAST SIMS'
        win_title = 'Fast Simulations'
        win_geometry = '500x270'
        win_resizable = False
        if not super().__init__(parent, name=name, win_title=win_title, win_geometry=win_geometry, win_resizable=win_resizable):
            return

        # Validate number
        self.validate_num_wrapper = (self.register(lambda newval: newval.isdigit()), '%S')

        # Widgets
        self.frm_sim = ttk.Frame(self, name='sim', padding=PAD)
        self.frm_sim.grid(row=0, column=0, sticky='nsew')
        self.widgets_sim()

        self.frm_status = ttk.Frame(self, name='status', padding=(PAD, 3, PAD, 5))
        self.frm_status.grid(row=1, column=0, sticky='ew')
        self.widgets_status()

        ## Exp Manager (from RAVA_APP_ANOM_INT)
        self.exp_mgr = self.master.exp_mgr
        self.exp_mgr.cbkreg_exp_finished(self.exp_finished)

        ## Start

        # Available groups
        self.groups_populate()

        # Variables
        self.sess_i = 0
        self.sess_n = 0
        self.sess_t0 = 0
        self.sess_types_idxs = []
        self.sess_types = []

        # Config
        self.var_sim_files_a.set(self.cfg.read('SIM_FAST', 'files_bytes_a'))
        self.var_sim_files_b.set(self.cfg.read('SIM_FAST', 'files_bytes_b'))

        # RNG and Feedback
        self.rng = None
        self.feedb = FEEDB_DUMMY()


    def close(self):
        # Close RAVA_SUBAPP
        super().close()


    def widgets_sim(self):
        self.frm_sim.columnconfigure([0], weight=1)
        self.frm_sim.columnconfigure([1], weight=10)
        self.frm_sim.rowconfigure([0,1,2,3,4], weight=1)

        # Files
        self.lb_sim_file_a = ttk.Label(self.frm_sim, text='RNG A')
        self.lb_sim_file_a.grid(row=0, column=0)

        self.var_sim_files_a = tk.StringVar(value='')
        self.en_sim_files_a = ttk.Entry(self.frm_sim, textvariable=self.var_sim_files_a)
        self.en_sim_files_a.grid(row=0, column=1, sticky='ew')

        self.bt_sim_files_a_search = ttk.Button(self.frm_sim, width=2, text='...', command=self.files_a_search)
        self.bt_sim_files_a_search.grid(row=0, column=2, padx=PAD)

        self.lb_sim_file_b = ttk.Label(self.frm_sim, text='RNG B')
        self.lb_sim_file_b.grid(row=1, column=0)

        self.var_sim_files_b = tk.StringVar(value='')
        self.en_sim_files_b = ttk.Entry(self.frm_sim, textvariable=self.var_sim_files_b)
        self.en_sim_files_b.grid(row=1, column=1, sticky='ew')

        self.bt_sim_files_b_search = ttk.Button(self.frm_sim, width=2, text='...', command=self.files_b_search)
        self.bt_sim_files_b_search.grid(row=1, column=2, padx=PAD)

        # Sess Group
        self.lb_sim_group = ttk.Label(self.frm_sim, text='Sess Group')
        self.lb_sim_group.grid(row=2, column=0)

        self.var_sim_group = tk.IntVar()
        self.cbb_sim_group = ttk.Combobox(self.frm_sim, values=[], textvariable=self.var_sim_group, width=10)
        self.cbb_sim_group.grid(row=2, column=1, sticky='w')
        self.cbb_sim_group.bind('<<ComboboxSelected>>', self.group_sel)
        self.cbb_sim_group.state(['readonly'])

        # Start
        self.bt_sim_start = ttk.Button(self.frm_sim, text='Start', command=self.sim_start)
        self.bt_sim_start.grid(row=3, column=0, columnspan=3)


    def widgets_status(self):
        self.frm_status.columnconfigure([0], weight=1)
        self.frm_status.rowconfigure([0], weight=1)

        self.var_status = tk.StringVar(value='')
        self.lb_status = ttk.Label(self.frm_status, relief=tk.RIDGE, anchor='e', textvariable=self.var_status)
        self.lb_status.grid(row=0, column=0, sticky='ew')


    def status_set(self, str):
        self.var_status.set(str + '  ')


    def sess_n_remaining(self, sess_group):
        part_n_remaining = self.exp_mgr.db.sess_get_part_n_remaining(sess_group)

        return part_n_remaining


    def groups_populate(self, tk_event=None):
        sess_groups = self.exp_mgr.db.groups_get(res_type='dol')['group']

        if len(sess_groups) == 0:
            self.lg.error('{}: No group available. Closing.'.format(self.name))
            tkm.showerror(parent=self, title='Error', message='No group avaliable. Create one with the Groups Subapp.')
            self.close()
            return

        # Update Combobox widgets
        self.cbb_sim_group['values'] = sess_groups

        # Select initial group
        self.var_sim_group.set(sess_groups[0])

        # Update status bar
        self.group_sel()


    def group_sel(self, tk_event=None):
        # Update status
        sess_group = self.var_sim_group.get()
        sess_n_remaining = self.sess_n_remaining(sess_group)
        required_bytes = self.group_required_bytes(sess_group)
        required_bytes_mega = required_bytes / 1000000

        sts = 'Group {}:  Requires 2 x {:.3f} MBytes;  Sessions to finish = {}'.format(sess_group, required_bytes_mega, sess_n_remaining)
        self.status_set(sts)


    def group_required_bytes(self, sess_group):
        # Get groups data
        goups_data = self.exp_mgr.db.groups_get(sess_group, res_type='lod')[0]
        sess_n_per_type = goups_data['sess_n_per_type']
        sess_types = goups_data['sess_types']

        # Calculate n for each exp
        sess_n_exp1 = sess_n_per_type if 'EXP_1' in sess_types else 0
        sess_n_exp2 = sess_n_per_type if 'EXP_2' in sess_types else 0
        sess_n_exp3 = sess_n_per_type if 'EXP_3' in sess_types else 0
        sess_n_exp4 = sess_n_per_type if 'EXP_4' in sess_types else 0

        required_bytes = BYTES_EXP_1 * sess_n_exp1 + BYTES_EXP_2 * sess_n_exp2 + BYTES_EXP_3 * sess_n_exp3 + BYTES_EXP_4 * sess_n_exp4
        return required_bytes


    def files_a_search(self):
        files_in0 = self.var_sim_files_a.get()
        try:
            file_in0 = eval(files_in0)[0]
        except:
            file_in0 = ''

        file_dir_in0 = os.path.dirname(file_in0) if file_in0 else ''
        files_in = tk.filedialog.askopenfilename(parent=self, initialdir=file_dir_in0, filetypes=[('Binary File', '.bin')], multiple=True)
        if files_in:
            self.var_sim_files_a.set(files_in)
            self.cfg.write('SIM_FAST', 'files_bytes_a', files_in)


    def files_b_search(self):
        files_in0 = self.var_sim_files_b.get()
        try:
            file_in0 = eval(files_in0)[0]
        except:
            file_in0 = ''

        file_dir_in0 = os.path.dirname(file_in0) if file_in0 else ''
        files_in = tk.filedialog.askopenfilename(parent=self, initialdir=file_dir_in0, filetypes=[('Binary File', '.bin')], multiple=True)
        if files_in:
            self.var_sim_files_b.set(files_in)
            self.cfg.write('SIM_FAST', 'files_bytes_b', files_in)


    def sim_start(self):
        # Get input data
        sess_group = self.var_sim_group.get()
        str_files_a = self.var_sim_files_a.get()
        str_files_b = self.var_sim_files_b.get()

        # Convert files str to list
        files_a = list(eval(str_files_a))
        files_b = list(eval(str_files_b))

        # Get data
        sess_n_remaining = self.sess_n_remaining(sess_group)

        # Test input
        if sess_n_remaining == 0:
            tkm.showerror(parent=self, title='Error',
                          message='All sessions from group {} have been colected'.format(sess_group))
            return

        for file_a in files_a:
            if not os.path.exists(file_a):
                tkm.showerror(parent=self, title='Error', message='Inexistent file A {}'.format(file_a))
                return

        for file_b in files_b:
            if not os.path.exists(file_b):
                tkm.showerror(parent=self, title='Error', message='Inexistent file B {}'.format(file_b))
                return

        # Save cfg
        self.cfg.write('SIM_FAST', 'files_bytes_a', str_files_a)
        self.cfg.write('SIM_FAST', 'files_bytes_b', str_files_b)

        # Create RNG from file
        self.rng = RNG_FROM_FILE(files_a, files_b)
        n_bytes_a, n_bytes_b = self.rng.bytes_available()

        # Enough bytes?
        self.sess_i = 0
        self.sess_n = sess_n_remaining
        required_bytes = self.group_required_bytes(sess_group)

        if n_bytes_a < required_bytes:
            tkm.showerror(parent=self, title='Error', message='RNG A Bytes are not enough. Provided={}, Needed={}'.format(n_bytes_a, required_bytes))
            return

        if n_bytes_b < required_bytes:
            tkm.showerror(parent=self, title='Error', message='RNG B Bytes are not enough. Provided={}, Needed={}'.format(n_bytes_b, required_bytes))
            return

        # Generate sess_types (random, without replacement)
        sess_type_n, sess_types = self.exp_mgr.db.groups_get_sess_types(sess_group)
        sess_n_per_type = self.exp_mgr.db.groups_get(sess_group, res_type='dol')['sess_n_per_type'][0]

        self.sess_types = sess_types
        self.sess_types_idxs = []
        for i in range(sess_n_per_type):
            self.sess_types_idxs.append(np.random.choice(sess_type_n, sess_type_n, replace=False))
        self.sess_types_idxs = np.hstack(self.sess_types_idxs)

        # Start Participant session
        self.sim_start_part(sess_group)


    def sim_start_part(self, sess_group):
        # Save time
        self.sess_t0 = time.perf_counter()

        # Assign sess_type
        sess_type_idx = self.sess_types_idxs[self.sess_i]
        sess_type = self.sess_types[sess_type_idx]

        # Initial data
        part_id = 0
        exp_init_data = {'part_id': part_id,
                         'part_name': 'simulation fast',
                         'sess_group': sess_group,
                         'sess_type': sess_type,
                         'sess_sham': False,
                         'part_hash_pointer': None,
                         'feedb_rng_target': None,       # Randomly selected at sessions' start
                         'simulation_fast': True,
                         'simulation_sess_i': self.sess_i,
                         'simulation_sess_n': self.sess_n,
                         'simulation_delay_min': 0
                         }

        # Start experiment
        self.exp_mgr.exp_start(exp_init_data, self.rng, self.feedb)


    def exp_finished(self, exp_data):
        # Get data
        sess_group = exp_data['sess_group']

        # Update status bar
        self.group_sel()

        # Update sess_i
        self.sess_i += 1

        # Debug time elapsed
        self.lg.debug('Time elapsed = {:.4f}s'.format(time.perf_counter() - self.sess_t0))

        # Debug amount of bytes used by the dummy RNG
        self.lg.debug('RNG idx = {}'.format(self.rng.bytes_idx))

        # Run another session
        if self.sess_i < self.sess_n:
            self.sim_start_part(sess_group)


rava_subapp_simulations_fast = {'class': RAVA_SUBAPP_SIMULATIONS_FAST,
                                'menu_title': 'Fast Simulations',
                                'show_button': True,
                                'use_rng': False
                                }