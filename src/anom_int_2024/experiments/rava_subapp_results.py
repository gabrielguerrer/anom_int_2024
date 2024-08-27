"""
Copyright (c) 2024 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
The Results sub-app enables listing the participant sessions and their
acquisition date. Upon clicking on a specific session, users can visualize the
corresponding star-indexed rating presented at this session's conclusion.

The sessions can be filtered according to their group and the participant ID.
"""

import tkinter as tk
from tkinter import ttk

from rng_rava.tk import RAVA_SUBAPP


# PARAMETERS

PAD = 10


# RAVA_SUBAPP_RESULTS

class RAVA_SUBAPP_RESULTS(RAVA_SUBAPP):

    cfg_default_str = ''

    def __init__(self, parent):
        ## Initialize RAVA_SUBAPP
        name = 'RAVA_SUBAPP RESULTS'
        win_title = 'Results'
        win_geometry = '500x450'
        win_resizable = False

        if not super().__init__(parent, name=name, win_title=win_title, win_geometry=win_geometry, win_resizable=win_resizable):
            return

        # Widgets
        self.rowconfigure([0], weight=8)
        self.rowconfigure([1], weight=1)
        self.columnconfigure([0], weight=1)
        self.widgets()

        ## Start

        # Experiment Manager (from RAVA_APP_ANOM_INT)
        self.exp_mgr = self.master.exp_mgr

        # Populate widgets contents
        self.widgets_populate()


    def widgets(self):
        self.frm_tree = ttk.Frame(self, name='frame_tree', padding=PAD)
        self.frm_tree.grid(row=0, column=0, sticky='nsew')
        self.frm_tree.columnconfigure([0], weight=1)
        self.frm_tree.rowconfigure([0], weight=1)

        # Treeview
        res_cols = ['dt_start', 'sess_group', 'part_id', 'feedb_stars']
        res_cols_width = [150, 100, 100, 100]

        self.tree_res = ttk.Treeview(self.frm_tree, columns=res_cols, selectmode='browse', height=7)
        self.tree_res.grid(row=0, column=0, sticky='nsew', pady=(PAD, 0))
        self.tree_res['show'] = 'headings'
        for i, col in enumerate(res_cols):
            self.tree_res.column(col, width=res_cols_width[i], stretch=False)
            self.tree_res.heading(col, text=col)

        self.scroll_res_y = ttk.Scrollbar(self.frm_tree, orient=tk.VERTICAL, command=self.tree_res.yview)
        self.scroll_res_y.grid(row=0, column=1, sticky='nsew')
        self.tree_res['yscrollcommand'] = self.scroll_res_y.set

        ## Filters
        self.lbf_filters = ttk.Labelframe(self, text=' Filters ', padding=PAD)
        self.lbf_filters.grid(row=1, column=0, sticky='nsew', padx=PAD, pady=(0, PAD))
        self.lbf_filters.columnconfigure([0,1,2,3], weight=1)
        self.lbf_filters.rowconfigure([0], weight=1)

        # sess_group
        self.lb_filter_group = ttk.Label(self.lbf_filters, text='group')
        self.lb_filter_group.grid(row=0, column=0)

        self.var_filter_group = tk.StringVar()
        self.cbb_filter_group = ttk.Combobox(self.lbf_filters, values=[], textvariable=self.var_filter_group, width=10)
        self.cbb_filter_group.grid(row=0, column=1)
        self.cbb_filter_group.bind('<<ComboboxSelected>>', self.filter_apply)
        self.cbb_filter_group.state(['readonly'])

        # part_id
        self.lb_filter_part = ttk.Label(self.lbf_filters, text='part_id')
        self.lb_filter_part.grid(row=0, column=2)

        self.var_filter_part = tk.StringVar()
        self.cbb_filter_part = ttk.Combobox(self.lbf_filters, values=[], textvariable=self.var_filter_part, width=10)
        self.cbb_filter_part.grid(row=0, column=3)
        self.cbb_filter_part.bind('<<ComboboxSelected>>', self.filter_apply)
        self.cbb_filter_part.state(['readonly'])


    def widgets_populate(self):
        sess_data_tuple = self.exp_mgr.db.sess_get_part_sessions(res_type='tuple')

        # Update tree
        for item in self.tree_res.get_children():
            self.tree_res.delete(item)
        for s in sess_data_tuple:
            s = list(s)
            sess_hash = s[0]
            res_data = s[1:]
            res_data[0] = str(res_data[0])[:16] # Trim seconds from datetime
            self.tree_res.insert('', 'end', iid=sess_hash, values=res_data)

        # Update comboboxes
        sess_data_dict = self.exp_mgr.db.sess_get_part_sessions(res_type='dol')
        groups = [''] + list(set(sess_data_dict['sess_group']))
        parts = [''] + list(set(sess_data_dict['part_id']))

        self.cbb_filter_group['values'] = groups
        self.cbb_filter_part['values'] = parts


    def filter_apply(self, tk_event=None):
        sess_group = self.var_filter_group.get()
        sess_group = None if sess_group == '' else sess_group

        part_id = self.var_filter_part.get()
        part_id = None if part_id == '' else part_id

        ## Populate tree

        # Get data with filters
        sess_data_tuple = self.exp_mgr.db.sess_get_part_sessions(sess_group=sess_group, part_id=part_id, res_type='tuple')

        # Update tree
        for item in self.tree_res.get_children():
            self.tree_res.delete(item)
        for s in sess_data_tuple:
            s = list(s)
            sess_hash = s[0]
            res_data = s[1:]
            res_data[0] = str(res_data[0])[:16] # Trim seconds from datetime
            self.tree_res.insert('', 'end', iid=sess_hash, values=res_data)


rava_subapp_results = {'class': RAVA_SUBAPP_RESULTS,
                       'menu_title': 'Results',
                       'show_button': True,
                       'use_rng': False
                       }