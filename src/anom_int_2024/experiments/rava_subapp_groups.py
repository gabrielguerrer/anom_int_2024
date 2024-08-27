"""
Copyright (c) 2024 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
This sub-app manages the experimental Groups. Each group is tied to a
preregistration document, reflecting the commitment to run a certain
number of experimental sessions of a certain type.

The group definition includes a listing of its constituent session types, the
number of sessions to be collected for each type, and the option to
automatically assign each session to one of the possible types.

For more information about the auto-assign feature, see the experiment manager
module.
"""

import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as tkm

from rng_rava.tk import RAVA_SUBAPP


# PARAMETERS

PAD = 10


# RAVA_SUBAPP_GROUPS

class RAVA_SUBAPP_GROUPS(RAVA_SUBAPP):

    cfg_default_str = ''

    def __init__(self, parent):
        ## Initialize RAVA_SUBAPP
        name = 'RAVA_SUBAPP GROUPS'
        win_title = 'Groups'
        win_geometry = '450x300'
        win_resizable = False
        if not super().__init__(parent, name=name, win_title=win_title, win_geometry=win_geometry, win_resizable=win_resizable):
            return

        # Validate number
        self.validate_num_wrapper = (self.register(lambda newval: newval.isdigit()), '%S')

        # Experiment Manager (from RAVA_APP_ANOM_INT)
        self.exp_mgr = self.master.exp_mgr

        # Widgets
        self.nb = ttk.Notebook(self, padding=PAD)
        self.nb.grid(row=0, column=0, sticky='nsew')
        self.nb.bind('<<NotebookTabChanged>>', self.notebook_tab_change)

        self.frm_view = ttk.Frame(self, name='view', padding=PAD)
        self.frm_view.grid(row=0, column=0, sticky='nsew')
        self.widgets_view()

        self.frm_add = ttk.Frame(self, name='add', padding=PAD)
        self.frm_add.grid(row=0, column=0, sticky='nsew')
        self.widgets_add()

        self.nb.add(self.frm_view, text=' View ')
        self.nb.add(self.frm_add, text=' Add ')


    def widgets_view(self):
        self.frm_view.columnconfigure([0], weight=1)
        self.frm_view.rowconfigure([0,2], weight=1)

        # Treeview
        group_cols = ['group', 'sess_types', 'sess_n_per_type', 'type_auto']
        group_cols_width = [50, 300, 130, 80]

        self.tree_groups = ttk.Treeview(self.frm_view, columns=group_cols, selectmode='browse', height=7)
        self.tree_groups.grid(row=0, column=0, sticky='ew', padx=(PAD, PAD//2), pady=(0, PAD//2))
        self.tree_groups['show'] = 'headings'
        for i, col in enumerate(group_cols):
            self.tree_groups.column(col, width=group_cols_width[i], stretch=False)
            self.tree_groups.heading(col, text=col)

        self.scroll_groups_y = ttk.Scrollbar(self.frm_view, orient=tk.VERTICAL, command=self.tree_groups.yview)
        self.scroll_groups_y.grid(row=0, column=1, sticky='ns')
        self.tree_groups['yscrollcommand'] = self.scroll_groups_y.set

        self.scroll_groups_x = ttk.Scrollbar(self.frm_view, orient=tk.HORIZONTAL, command=self.tree_groups.xview)
        self.scroll_groups_x.grid(row=1, column=0, sticky='ew', padx=(PAD, 0))
        self.tree_groups['xscrollcommand'] = self.scroll_groups_x.set

        # Delete
        self.bt_delete = ttk.Button(self.frm_view, text='Delete', command=self.group_delete)
        self.bt_delete.grid(row=2, column=0, columnspan=2, pady=(PAD, 0))


    def widgets_add(self):
        self.frm_add.columnconfigure([0,1,2], weight=1)
        self.frm_add.rowconfigure([1,2,3,4], weight=1)

        # Group
        self.lb_add_group_ = ttk.Label(self.frm_add, text='Group')
        self.lb_add_group_.grid(row=1, column=0, sticky='w', padx=(PAD,0))

        self.var_add_group = tk.IntVar(value=1)
        self.sb_add_group = ttk.Spinbox(self.frm_add, width=7, from_=1, to=1000, increment=1, textvariable=self.var_add_group, validate='key', validatecommand=self.validate_num_wrapper)
        self.sb_add_group.grid(row=1, column=1, sticky='w')

        # N per type
        self.lb_add_npt = ttk.Label(self.frm_add, text='N Sess\n per Type')
        self.lb_add_npt.grid(row=2, column=0, sticky='w', padx=(PAD,0))

        self.var_add_npt = tk.IntVar(value=10)
        self.sb_add_npt = ttk.Spinbox(self.frm_add, width=7, from_=1, to=10000, increment=10, textvariable=self.var_add_npt)
        self.sb_add_npt.grid(row=2, column=1, sticky='w')

        # Type auto
        self.var_add_auto = tk.BooleanVar()
        self.cb_part_test = ttk.Checkbutton(self.frm_add, text=' Type = Auto', variable=self.var_add_auto)
        self.cb_part_test.grid(row=3, column=0, columnspan=2, sticky='w', padx=(PAD,0))

        # Types
        self.lb_add_type = ttk.Label(self.frm_add, text='Sess Types')
        self.lb_add_type.grid(row=0, column=2, sticky='w', padx=(PAD,0))

        self.var_add_types = tk.StringVar(value=[])
        self.lbox_add_type = tk.Listbox(self.frm_add, listvariable=self.var_add_types, selectmode='extended', height=5)
        self.lbox_add_type.grid(row=1, column=2, rowspan=3, sticky='nsew', padx=(PAD, 0), pady=PAD)

        self.scl_add_type = ttk.Scrollbar(self.frm_add, orient=tk.VERTICAL, command=self.lbox_add_type.yview)
        self.scl_add_type.grid(row=1, column=3, rowspan=3, sticky='ns', pady=PAD)
        self.lbox_add_type['yscrollcommand'] = self.scl_add_type.set

        # Add
        self.bt_add = ttk.Button(self.frm_add, text='Add', command=self.group_add)
        self.bt_add.grid(row=4, column=0, columnspan=3)


    def notebook_tab_change(self, tk_event=None):
        if 'view' in self.nb.select():
            self.group_populate()

        elif 'add' in self.nb.select():
            self.sess_type_populate()


    def sess_type_populate(self):
        sess_types_dict = self.exp_mgr.mgr_exps_available()
        self.var_add_types.set(list(sess_types_dict.keys()))


    def group_populate(self):
        # Get group data
        data = self.exp_mgr.db.groups_get()

        # Clear all entries
        for item in self.tree_groups.get_children():
            self.tree_groups.delete(item)

        # Insert data
        for d in data:
            group = d[0]
            self.tree_groups.insert('', 'end', iid=group, values=list(d))


    def group_add(self):

        # Get input
        group = self.var_add_group.get()
        sess_type_idxs = self.lbox_add_type.curselection()
        sess_n_per_type = self.var_add_npt.get()
        type_auto = self.var_add_auto.get()

        # Test input
        if sess_n_per_type == 0:
            tkm.showerror(parent=self, title='Error', message='Please provide the session N per type')
            return

        if len(sess_type_idxs) == 0:
            tkm.showerror(parent=self, title='Error', message='Please select the desired session types')
            return

        # Group already exists?
        if len(self.exp_mgr.db.groups_get(group)):
            tkm.showerror(parent=self, title='Error', message='Group {} already exists'.format(group))
            return

        # Process input
        sess_types = [self.lbox_add_type.get(i) for i in sess_type_idxs]
        sess_types_str = ','.join(sess_types)

        data_dict = {'group':group, 'sess_types':sess_types_str, 'sess_n_per_type':sess_n_per_type, 'type_auto':type_auto}

        # Add group
        self.exp_mgr.db.groups_add(data_dict)


    def group_delete(self):
        # Get selected group
        sel = self.tree_groups.selection()
        if not sel:
            return
        group = int(sel[0])

        # Delete group
        if tkm.askyesno(parent=self, title='Delete', message='Confirm group {} deletion?'.format(group)):
            self.exp_mgr.db.groups_del(group)

            # Update treeview widget
            self.group_populate()


rava_subapp_groups = {'class': RAVA_SUBAPP_GROUPS,
                      'menu_title': 'Groups',
                      'show_button': True,
                      'use_rng': False
                      }