"""
Copyright (c) 2024 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
The Experiments sub-app implements the interface for running experimental
sessions and collecting data.

Two types of sessions are supported: participant and sham. In participant
sessions, an individual observes the visual feedback with the intent to enlarge
the circle's diameter.  Sham sessions are functionally identical to participant
sessions in terms of software. The key distinction is the absence of an
observer -- no individual watches the feedback during a sham session.

Each sham session is intricately linked to a participant session, inheriting
its distinctive parameters, including sess_type, and feedb_rng_target. The
standard procedure involves collecting the associated sham session immediately
following the participant one.
"""

import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as tkm

from rng_rava.tk import RAVA_SUBAPP


# PARAMETERS

PAD = 10


# RAVA_SUBAPP_EXPERIMENTS

class RAVA_SUBAPP_EXPERIMENTS(RAVA_SUBAPP):

    cfg_default_str = '''
    [EXPS_SUBAPP]
    sess_group_last = 1
    '''

    def __init__(self, parent):
        # Initialize RAVA_SUBAPP
        name = 'RAVA_SUBAPP EXPS'
        win_title = 'New Session'
        win_geometry = '390x270'
        win_resizable = False
        if not super().__init__(parent, name=name, win_title=win_title, win_geometry=win_geometry, win_resizable=win_resizable):
            return

        # Config
        self.sess_group_last = self.cfg.read('EXPS_SUBAPP', 'sess_group_last', int)

        # Common
        self.var_group = tk.IntVar(value=self.sess_group_last)

        # Validate number
        self.validate_num_wrapper = (self.register(lambda newval: newval.isdigit()), '%S')

        # Widgets
        self.nb = ttk.Notebook(self, padding=PAD)
        self.nb.grid(row=0, column=0, sticky='nsew')
        self.nb.bind('<<NotebookTabChanged>>', self.notebook_tab_change)

        self.frm_part = ttk.Frame(self, name='exp_part', padding=PAD)
        self.frm_part.grid(row=0, column=0, sticky='nsew')
        self.widgets_part()
        self.nb.add(self.frm_part, text=' Participant ')

        self.frm_sham = ttk.Frame(self, name='exp_sham', padding=PAD)
        self.frm_sham.grid(row=0, column=0, sticky='nsew')
        self.widgets_sham()
        self.nb.add(self.frm_sham, text=' Sham ')

        self.frm_status = ttk.Frame(self, name='exp_status', padding=(PAD, 3, PAD, 5))
        self.frm_status.grid(row=1, column=0, sticky='ew')
        self.widgets_status()

        ## Exp Manager (from RAVA_APP_ANOM_INT)
        self.exp_mgr = self.master.exp_mgr
        self.exp_mgr.cbkreg_exp_finished(self.exp_finished)

        ## Start

        # Available groups
        self.groups_populate()


    def close(self):
        # Close RAVA_SUBAPP
        super().close()


    def widgets_part(self):
        self.frm_part.columnconfigure([0,1,2], weight=1)
        self.frm_part.rowconfigure([0,1,2,3,4], weight=1)

        # Part Name
        self.lb_part_name = ttk.Label(self.frm_part, text='Part Name')
        self.lb_part_name.grid(row=0, column=0, sticky='w', padx=(PAD,0))

        self.var_part_name = tk.StringVar()
        self.en_part_name = ttk.Entry(self.frm_part, width=30, textvariable=self.var_part_name)
        self.en_part_name.grid(row=0, column=1, columnspan=2, sticky='w')

        # Part ID
        self.lb_part_id = ttk.Label(self.frm_part, text='Part ID')
        self.lb_part_id.grid(row=1, column=0, sticky='w', padx=(PAD,0))

        self.var_part_id = tk.StringVar(value='')
        self.en_part_id = ttk.Entry(self.frm_part, width=12, textvariable=self.var_part_id, validate='key', validatecommand=self.validate_num_wrapper)
        self.en_part_id.grid(row=1, column=1, sticky='w')

        # Sess Group
        self.lb_part_group = ttk.Label(self.frm_part, text='Sess Group')
        self.lb_part_group.grid(row=2, column=0, sticky='w', padx=(PAD,0))

        self.cbb_part_group = ttk.Combobox(self.frm_part, values=[], textvariable=self.var_group, width=10)
        self.cbb_part_group.grid(row=2, column=1, sticky='w')
        self.cbb_part_group.bind('<<ComboboxSelected>>', self.part_group_sel)
        self.cbb_part_group.state(['readonly'])

        # Sess Type
        self.lb_part_sess_type = ttk.Label(self.frm_part, text='Sess Type')
        self.lb_part_sess_type.grid(row=3, column=0, sticky='w', padx=(PAD,0))

        self.cbb_part_sess_type = ttk.Combobox(self.frm_part, width=10)
        self.cbb_part_sess_type.grid(row=3, column=1, sticky='w')
        self.cbb_part_sess_type.state(['readonly'])

        # Start
        self.bt_part_sess_start = ttk.Button(self.frm_part, text='Start', command=self.exp_part_start)
        self.bt_part_sess_start.grid(row=4, column=0, columnspan=3)


    def widgets_sham(self):
        self.frm_sham.columnconfigure([0,1,2], weight=1)
        self.frm_sham.rowconfigure([0,1,2,3,4], weight=1)

        # Sess Group
        self.lb_sham_group = ttk.Label(self.frm_sham, text='Sess Group')
        self.lb_sham_group.grid(row=0, column=0, sticky='w', padx=(PAD,0))

        self.cbb_sham_group = ttk.Combobox(self.frm_sham, values=[], textvariable=self.var_group, width=10)
        self.cbb_sham_group.grid(row=0, column=1, sticky='w')
        self.cbb_sham_group.bind('<<ComboboxSelected>>', self.sham_group_sel)
        self.cbb_sham_group.state(['readonly'])

        # Spacers
        self.lb_sham_spacer1 = ttk.Label(self.frm_sham, text=' ')
        self.lb_sham_spacer1.grid(row=1, column=0)

        self.lb_sham_spacer2 = ttk.Label(self.frm_sham, text=' ')
        self.lb_sham_spacer2.grid(row=2, column=0)

        self.lb_sham_spacer3 = ttk.Label(self.frm_sham, text=' ')
        self.lb_sham_spacer3.grid(row=3, column=0)

        # Start
        self.bt_sham_sess_start = ttk.Button(self.frm_sham, text='Start', command=self.exp_sham_start)
        self.bt_sham_sess_start.grid(row=4, column=0, columnspan=4)


    def widgets_status(self):
        self.frm_status.columnconfigure([0], weight=1)
        self.frm_status.rowconfigure([0], weight=1)

        self.var_status = tk.StringVar(value='')
        self.lb_status = ttk.Label(self.frm_status, relief=tk.RIDGE, anchor='e', textvariable=self.var_status)
        self.lb_status.grid(row=0, column=0, sticky='ew')


    def status_set(self, str):
        self.var_status.set(str + '  ')


    def groups_populate(self, tk_event=None):
        sess_groups = self.exp_mgr.db.groups_get(res_type='dol')['group']

        if len(sess_groups) == 0:
            self.lg.error('{}: No group available. Closing.'.format(self.name))
            tkm.showerror(parent=self, title='Error', message='No group avaliable. Create one with the Groups Subapp.')
            self.close()
            return

        # Update Combobox widgets
        self.cbb_part_group['values'] = sess_groups
        self.cbb_sham_group['values'] = sess_groups

        # Select initial group
        sess_group = self.var_group.get()
        if sess_group not in sess_groups:
            self.var_group.set(sess_groups[0])


    def part_group_sel(self, tk_event=None):
        # Find remaining sessions
        sess_group = self.var_group.get()
        sess_n_remaining = self.exp_mgr.db.sess_get_part_n_remaining(sess_group)
        sts = 'Participant sessions to finish group {} = {}'.format(sess_group, sess_n_remaining)
        self.status_set(sts)

        # Update session_type Combobox
        if sess_n_remaining is not None:
            sess_type_auto = self.exp_mgr.db.groups_get(group=sess_group, res_type='dol')['type_auto'][0]
            if sess_type_auto:
                self.cbb_part_sess_type['values'] = ['Auto']
                self.cbb_part_sess_type.set('Auto')
            else:
                _, group_session_types = self.exp_mgr.db.groups_get_sess_types(group=sess_group)
                self.cbb_part_sess_type['values'] = group_session_types
                self.cbb_part_sess_type.set(group_session_types[0])


    def sham_group_sel(self, tk_event=None):
        # Find missing sessions
        sess_group = self.var_group.get()
        sess_n_missing, _ = self.exp_mgr.db.sess_get_sham_missing(sess_group)
        sts = 'Control sessions missing in group {} = {}'.format(sess_group, sess_n_missing)
        self.status_set(sts)


    def notebook_tab_change(self, tk_event=None):
        if 'part' in self.nb.select():
            self.part_group_sel()

        elif 'sham' in self.nb.select():
            self.sham_group_sel()


    def exp_part_start(self):
        # Get data
        part_name = self.var_part_name.get()
        part_id = self.var_part_id.get()
        part_id = int(part_id) if part_id.isdigit() else 0
        sess_group = self.var_group.get()
        sess_type = self.cbb_part_sess_type.get()

        # Test input
        if not len(part_name):
            tkm.showerror(parent=self, title='Error', message='Please provide the participant\'s first name')
            return

        if part_id == 0:
            tkm.showerror(parent=self, title='Error', message='Please provide the participant\'s ID')
            return

        # Save data
        self.cfg.write('EXPS_SUBAPP', 'sess_group_last', sess_group)

        # Start
        self.exp_mgr.exp_start_part(part_id, part_name, sess_group, sess_type)


    def exp_sham_start(self):
        # Get data
        sess_group = self.var_group.get()

        # Save data
        self.cfg.write('EXPS_SUBAPP', 'sess_group_last', sess_group)

        # Start
        self.exp_mgr.exp_start_sham(sess_group)


    def exp_finished(self, exp_data):
        # Update widgets
        self.notebook_tab_change()


rava_subapp_experiments = {'class': RAVA_SUBAPP_EXPERIMENTS,
                           'menu_title': 'New Session',
                           'show_button': True,
                           'use_rng': True
                           }