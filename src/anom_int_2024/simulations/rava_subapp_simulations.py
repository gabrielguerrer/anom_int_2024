"""
Copyright (c) 2024 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
The simulation module allows for collecting experimental sessions sequentially,
which is crucial for identifying potential systematic errors during standard
data taking.

To generate simulated sessions, first create an experimental group specifying
the desired experiment types and the number of sessions per type. Then, select
the experiment group in the simulation window and click 'Start'. All sessions
will be collected in one go.
"""

import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as tkm

from rng_rava.tk import RAVA_SUBAPP


# PARAMETERS

PAD = 10


# RAVA_SUBAPP_SIMULATIONS

class RAVA_SUBAPP_SIMULATIONS(RAVA_SUBAPP):

    cfg_default_str = '''
    [SIM]
    sess_delay_min = 0
    '''


    def __init__(self, parent):

        # Initialize RAVA_SUBAPP
        name = 'RAVA_SUBAPP SIMS'
        win_title = 'Simulations'
        win_geometry = '390x200'
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
        self.groups_populate()

        # Variables
        self.sess_i = 0
        self.sess_n = 0
        self.sess_delay_min = 0

        # Config
        self.var_sim_sess_delay.set(self.cfg.read('SIM', 'sess_delay_min'))


    def close(self):
        # Close RAVA_SUBAPP
        super().close()


    def widgets_sim(self):
        self.frm_sim.columnconfigure([0,1], weight=1)
        self.frm_sim.rowconfigure([0,1,2], weight=1)

        # Sess Group
        self.lb_sim_group = ttk.Label(self.frm_sim, text='Sess Group')
        self.lb_sim_group.grid(row=0, column=0, sticky='w', padx=(PAD,0))

        self.var_sim_group = tk.IntVar()
        self.cbb_sim_group = ttk.Combobox(self.frm_sim, values=[], textvariable=self.var_sim_group, width=10)
        self.cbb_sim_group.grid(row=0, column=1, sticky='w')
        self.cbb_sim_group.bind('<<ComboboxSelected>>', self.group_sel)
        self.cbb_sim_group.state(['readonly'])

        # Sess Delay
        self.lb_sim_sess_delay = ttk.Label(self.frm_sim, text='Sess delay (min)')
        self.lb_sim_sess_delay.grid(row=1, column=0, sticky='w', padx=(PAD,0))

        self.var_sim_sess_delay = tk.IntVar(value=0)
        self.sb_sim_sess_delay = ttk.Spinbox(self.frm_sim, width=9, from_=0, to=600, increment=1, textvariable=self.var_sim_sess_delay, validate='key', validatecommand=self.validate_num_wrapper)
        self.sb_sim_sess_delay.grid(row=1, column=1, sticky='w')

        # Start
        self.bt_sim_start = ttk.Button(self.frm_sim, text='Start', command=self.sim_start)
        self.bt_sim_start.grid(row=2, column=0, columnspan=2)


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
        sham_n_missing, _ = self.exp_mgr.db.sess_get_sham_missing(sess_group)
        sess_n_remaining = 2*part_n_remaining + sham_n_missing

        return sess_n_remaining


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
        sts = 'Sessions (part + sham) to finish group {} = {}'.format(sess_group, sess_n_remaining)
        self.status_set(sts)


    def sim_start(self):
        # Get input data
        sess_group = self.var_sim_group.get()
        sess_delay_min = self.var_sim_sess_delay.get()

        # Get data
        sess_n_remaining = self.sess_n_remaining(sess_group)
        sham_n_missing, sham_hashes_missing = self.exp_mgr.db.sess_get_sham_missing(sess_group)

        # Test input
        if sess_n_remaining == 0:
            tkm.showerror(parent=self, title='Error',
                          message='All sessions from group {} have been colected'.format(sess_group))
            return

        # Save cfg
        self.cfg.write('SIM', 'sess_delay_min', sess_delay_min)

        # Start
        self.sess_i = 0
        self.sess_n = sess_n_remaining
        self.sess_delay_min = sess_delay_min

        if sham_n_missing:
            # Sham session
            self.sim_start_sham(sess_group, sham_hashes_missing[-1])
        else:
            # Participant session
            self.sim_start_part(sess_group)


    def sim_start_part(self, sess_group):
        # Automatically assign sess_type
        part_id = 0
        sess_type = self.exp_mgr.mgr_part_sess_type_auto(sess_group, part_id)

        # Initial data
        exp_init_data = {'part_id': part_id,
                         'part_name': 'simulation',
                         'sess_group': sess_group,
                         'sess_type': sess_type,
                         'sess_sham': False,
                         'part_hash_pointer': None,
                         'feedb_rng_target': None,       # Randomly selected at sessions' start
                         'simulation_fast': False,
                         'simulation_sess_i': self.sess_i,
                         'simulation_sess_n': self.sess_n,
                         'simulation_delay_min': self.sess_delay_min
                         }

        # Start experiment
        self.exp_mgr.exp_start(exp_init_data, self.exp_mgr.rng, self.exp_mgr.win_feedb_circle)


    def sim_start_sham(self, sess_group, part_hash_pointer):
        # Get parameters from the associated part session
        sess_type, feedb_rng_target = self.exp_mgr.db.sess_get_part_initial_pars(part_hash_pointer)

        # Initial data
        exp_init_data = {'part_id': 0,
                         'part_name': 'simulation',
                         'sess_group': sess_group,
                         'sess_type': sess_type,                            # Inherits the associated part session value
                         'sess_sham': True,
                         'part_hash_pointer': part_hash_pointer,
                         'feedb_rng_target': feedb_rng_target,              # Inherits the associated part session value
                         'simulation_fast': False,
                         'simulation_sess_i': self.sess_i,
                         'simulation_sess_n': self.sess_n,
                         'simulation_delay_min': self.sess_delay_min
                         }

        # Start experiment
        self.exp_mgr.exp_start(exp_init_data, self.exp_mgr.rng, self.exp_mgr.win_feedb_circle)


    def exp_finished(self, exp_data):
        # Get data
        sess_group = exp_data['sess_group']
        sess_sham = exp_data['sess_sham']
        sess_hash = exp_data['sess_hash']

        # Update status bar
        self.group_sel()

        # Update sess_i
        self.sess_i += 1

        # Just Finished a part session?
        if sess_sham == False:
            # Close star feedback window
            self.exp_mgr.win_feedb_star.hide()

            # Run associated sham session
            if self.sess_i < self.sess_n:
                self.sim_start_sham(sess_group, sess_hash)

        else:
            # Run part session
            if self.sess_i < self.sess_n:
                self.sim_start_part(sess_group)


rava_subapp_simulations = {'class': RAVA_SUBAPP_SIMULATIONS,
                           'menu_title': 'Simulations',
                           'show_button': True,
                           'use_rng': True
                           }