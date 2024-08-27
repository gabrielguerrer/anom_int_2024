"""
Copyright (c) 2024 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
The WINDOW_ANALYSIS class implements an interface for analyzing experimental
sessions. Initially, the application connects to a database file containing the
experimental sessions. Users can then apply desired filters to the data and
select the sessions to be analyzed. The analysis tools are accessible in the
right side panel, where users can choose between four different analysis modes:
preregistered, explorarory A, explorarory B, and fast simulation.

In the preregistered mode, the sessions are processed into p-values using the
following association between experiment type and function:
- Experiments 1 and 4: analyze_exp_bit_bias_2tail
- Experiment 2: analyze_exp_bit_bias_middleinvert_2tail
- Experiment 3: analyze_exp_byte_bias
The p-values are then combined using Fisher's method and displayed in the
results textbox.

In exploratory A mode, users can:
- Manually select a specific type of analysis for the chosen sessions
- Choose to analyze the RAVA's parallel core data
- Transform the p-values to their complementary value 1 - p
- Invert the byte selection in Experiment 4 sessions
- Plot the p-values for each session and their cumulative combination, with an
  option to display the y-axis on a logarithmic scale

In Exploratory Mode B, users can generate plots for individual sessions,
displaying the 5-minute cumulative evolution of the variable of interest along
with the associated two-tailed p-value. Available options include:
- Forcing the variable of interest to be either bit bias or byte bias,
  regardless of the experiment type
- Choosing to also plot RAVA's parallel core data
- Inverting the byte selection in Experiment 4 sessions
- Replacing the cumulative p-value with feedback magnitude, calculated as
  1 - sqrt(p)

In the fast simulation, many experiments are generated to evaluate the
uniformity of p'-values. This is achieved by binning the p'-values and
conducting a chi-square test. Additionally, the p'-values are sorted to
facilitate comparison between the empirical cumulative distribution function
and the expected linear distribution. The 'Comb N' option specifies the number
of sessions to be combined into p'-values. For example, if there are a total of
N=60,000 exp1 sessions and 'Comb N' is set to 60, the uniformity of 1,000
p'-values will be evaluated.
"""

import os
import numpy as np
import matplotlib.pyplot as plt

import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as tkm
import tkinter.filedialog as tkfd

from rng_rava.tk import RAVA_CFG

from anom_int_2024.experiments import FILES_PATH
from anom_int_2024.analysis import ANA_DB, plot_p_cumulative
from anom_int_2024.analysis import bit_bias_2tail_bytein, byte_bias_bytein
from anom_int_2024.analysis import analyze_exp, exps_bytes_definition
from anom_int_2024.analysis import analyze_exp_bit_bias_2tail, analyze_exp_bit_bias_middleinvert_2tail, analyze_exp_byte_bias
from anom_int_2024.analysis import fisher_combine, plot_p_uniformity, plot_single_sess


## PARAMETERS

PAD = 10

VIEW_VARS = ['sess_hash',
             'dt_start',
             'part_id',
             'sess_group',
             'sess_type',
             'sess_sham',
             'part_hash_pointer',
             'feedb_rng_target',
             'rng_sn'
             ]

ANA_TYPES = ['Auto',
             'Bit Bias (EXP 1,4)',
             'Bit Bias MInv (EXP 2)',
             'Byte Bias (EXP 3)'
             ]

D_ANA_FUNCTIONS = dict(zip(ANA_TYPES,
                           [analyze_exp,
                            analyze_exp_bit_bias_2tail,
                            analyze_exp_bit_bias_middleinvert_2tail,
                            analyze_exp_byte_bias
                           ]))


## RAVA_SUBAPP_ANALYSIS

class WINDOW_ANALYSIS(tk.Tk):

    cfg_default_str = '''
    [ANALYSIS]
    filename_db_last =
    '''

    def __init__(self, title):
        # Initialize Tk Window
        super().__init__()
        self.title(title)
        self.geometry('1400x800')
        self.option_add('*tearOff', tk.FALSE)
        self.rowconfigure([1], weight=1)
        self.columnconfigure([0,1], weight=1)
        self.protocol('WM_DELETE_WINDOW', self.close)

        # Validate number
        self.validate_num_wrapper = (self.register(lambda newval: newval.isdigit()), '%S')

        # CFG
        filename_cfg = os.path.join(FILES_PATH, 'anom_int_2024_ana.cfg')
        self.cfg = RAVA_CFG(filename_cfg, self.cfg_default_str)

        # Vars
        self.data_n = 0
        self.data_selectall_toggle = False

        self.ana_last_hashes = []
        self.ana_last_pars = {}
        self.ana_last_pvals = {}
        self.plots = []

        # Widgets
        self.frm_db_sel = ttk.Labelframe(self, text='Database', padding=PAD)
        self.frm_db_sel.grid(row=0, column=0, sticky='nsew', padx=PAD, pady=PAD)
        self.widgets_db_sel()

        self.frm_db_data = ttk.Labelframe(self, text='Data', padding=PAD)
        self.frm_db_data.grid(row=1, column=0, sticky='nsew', padx=PAD)
        self.widgets_db_data()

        self.frm_db_filter = ttk.Labelframe(self, text='Filter', padding=PAD)
        self.frm_db_filter.grid(row=2, column=0, sticky='nsew', padx=PAD, pady=PAD)
        self.widgets_db_filter()

        self.frm_ana = ttk.Labelframe(self, text='Analysis')
        self.frm_ana.grid(row=1, column=1, rowspan=2, sticky='nsew', padx=(0, PAD), pady=(0, PAD))
        self.widgets_analysis()

        # Key binds
        self.bind('<Control-Key-p>', lambda event=None: self.plots_close())

        # Init
        self.db = ANA_DB()
        self.var_db_file.set(self.cfg.read('ANALYSIS', 'filename_db_last'))


    def close(self):
        self.plots_close()
        self.destroy()


    def plots_close(self):
        for fig in self.plots:
            plt.close(fig)
            del fig


    def widgets_db_sel(self):
        self.frm_db_sel.rowconfigure([0], weight=1)
        self.frm_db_sel.columnconfigure([0], weight=1)

        self.var_db_file = tk.StringVar()
        self.en_db_file = ttk.Entry(self.frm_db_sel, textvariable=self.var_db_file, width=10)
        self.en_db_file.grid(row=0, column=0, sticky='ew', padx=PAD)

        self.bt_db_search = ttk.Button(self.frm_db_sel, text='...', command=self.db_search)
        self.bt_db_search.grid(row=0, column=1, padx=PAD, pady=PAD)

        self.bt_db_connect = ttk.Button(self.frm_db_sel, text='Connect', command=self.db_connect)
        self.bt_db_connect.grid(row=0, column=2, padx=PAD, pady=PAD)


    def widgets_db_data(self):
        self.frm_db_data.rowconfigure([0], weight=1)
        self.frm_db_data.columnconfigure([0], weight=1)

        self.cols_tree_data_width = [115, 170, 100, 100, 100, 115, 100, 100, 100]
        self.cols_tree_data = VIEW_VARS

        self.tree_data = ttk.Treeview(self.frm_db_data, columns=self.cols_tree_data, selectmode='extended', show='headings')
        self.tree_data.grid(row=0, column=0, columnspan=2, pady=(0,PAD), sticky='ns')
        for i, col in enumerate(self.cols_tree_data):
            self.tree_data.column(col, width=self.cols_tree_data_width[i], stretch=False)
            self.tree_data.heading(col, text=col)
        self.tree_data.tag_bind('data', '<<TreeviewSelect>>', self.data_selection_label)

        self.scroll_data_x = ttk.Scrollbar(self.frm_db_data, orient=tk.HORIZONTAL, command=self.tree_data.xview)
        self.scroll_data_x.grid(row=1, column=0, columnspan=2, sticky='ew')

        self.scroll_data_y = ttk.Scrollbar(self.frm_db_data, orient=tk.VERTICAL, command=self.tree_data.yview)
        self.scroll_data_y.grid(row=0, column=2, sticky='ns')

        self.tree_data['xscrollcommand'] = self.scroll_data_x.set
        self.tree_data['yscrollcommand'] = self.scroll_data_y.set

        self.data_entries_str = '{} Entries ; {} Filtered ; {} Selected'
        self.lb_data_entries = ttk.Label(self.frm_db_data, text=self.data_entries_str.format(0, 0, 0))
        self.lb_data_entries.grid(row=2, column=0, sticky='nsew')

        self.bt_data_selectall = ttk.Button(self.frm_db_data, text='Select all', command=self.data_select_all)
        self.bt_data_selectall.grid(row=2, column=1, padx=PAD, pady=(PAD, 0))


    def widgets_db_filter(self):
        self.frm_db_filter.rowconfigure([0], weight=1)
        self.frm_db_filter.columnconfigure([0,1,2,3,4,5,6,7,8], weight=1)

        # sess_group
        self.lb_filt_sess_group = ttk.Label(self.frm_db_filter, text='sess_group')
        self.lb_filt_sess_group.grid(row=0, column=0, pady=PAD)

        self.cbb_filt_sess_group = ttk.Combobox(self.frm_db_filter, width=12)
        self.cbb_filt_sess_group.grid(row=0, column=1)
        self.cbb_filt_sess_group.bind('<<ComboboxSelected>>', self.data_populate)
        self.cbb_filt_sess_group.state(['readonly'])

        # sess_type
        self.lb_filt_sess_type = ttk.Label(self.frm_db_filter, text='sess_type')
        self.lb_filt_sess_type.grid(row=0, column=2, pady=PAD)

        self.cbb_filt_sess_type = ttk.Combobox(self.frm_db_filter, width=12)
        self.cbb_filt_sess_type.grid(row=0, column=3)
        self.cbb_filt_sess_type.bind('<<ComboboxSelected>>', self.data_populate)
        self.cbb_filt_sess_type.state(['readonly'])

        # sess_sham
        self.lb_filt_sess_sham = ttk.Label(self.frm_db_filter, text='sess_sham')
        self.lb_filt_sess_sham.grid(row=0, column=4, pady=PAD)

        self.cbb_filt_sess_sham = ttk.Combobox(self.frm_db_filter, width=12)
        self.cbb_filt_sess_sham.grid(row=0, column=5)
        self.cbb_filt_sess_sham.bind('<<ComboboxSelected>>', self.data_populate)
        self.cbb_filt_sess_sham.state(['readonly'])

        # part_id
        self.lb_filt_part_id = ttk.Label(self.frm_db_filter, text='part_id')
        self.lb_filt_part_id.grid(row=0, column=6, pady=PAD)

        self.cbb_filt_part_id = ttk.Combobox(self.frm_db_filter, width=12)
        self.cbb_filt_part_id.grid(row=0, column=7)
        self.cbb_filt_part_id.bind('<<ComboboxSelected>>', self.data_populate)
        self.cbb_filt_part_id.state(['readonly'])

        # Clear button
        self.bt_filt_clear = ttk.Button(self.frm_db_filter, text='Clear', command=self.filter_clear)
        self.bt_filt_clear.grid(row=0, column=8)


    def widgets_analysis(self):
        self.frm_ana.rowconfigure([0], weight=2)
        self.frm_ana.rowconfigure([2,3], weight=1)
        self.frm_ana.columnconfigure([0], weight=1)

        # Notebook analysis
        self.nb_ana = ttk.Notebook(self.frm_ana, padding=PAD)
        self.nb_ana.grid(row=0, column=0, columnspan=2, sticky='nsew')

        self.frm_ana_prereg = ttk.Frame(self.frm_ana, padding=PAD)
        self.frm_ana_prereg.grid(row=0, column=0, sticky='nsew')
        self.widgets_analysis_prereg()

        self.frm_ana_explo1 = ttk.Frame(self.frm_ana, padding=PAD)
        self.frm_ana_explo1.grid(row=0, column=0, sticky='nsew', padx=(0, PAD))
        self.widgets_analysis_explo1()

        self.frm_ana_explo2 = ttk.Frame(self.frm_ana, padding=PAD)
        self.frm_ana_explo2.grid(row=0, column=0, sticky='nsew', padx=(0, PAD))
        self.widgets_analysis_explo2()

        self.frm_ana_sim = ttk.Frame(self.frm_ana, padding=PAD)
        self.frm_ana_sim.grid(row=0, column=0, sticky='nsew', padx=(0, PAD))
        self.widgets_analysis_fsim()

        self.nb_ana.add(self.frm_ana_prereg, text=' Prereg ')        
        self.nb_ana.add(self.frm_ana_explo1, text=' Explo A ')
        self.nb_ana.add(self.frm_ana_explo2, text=' Explo B ')
        self.nb_ana.add(self.frm_ana_sim, text=' Fast Sim ')

        # Results text
        self.lb_ana_res = ttk.Label(self.frm_ana, text='Results')
        self.lb_ana_res.grid(row=1, column=0, columnspan=2, sticky='w', padx=PAD)

        self.txt_ana_res = tk.Text(self.frm_ana, width=10, height=10)
        self.txt_ana_res.grid(row=2, column=0, sticky='nsew', padx=(PAD,0), pady=PAD)

        self.scy_ana_res = ttk.Scrollbar(self.frm_ana, orient=tk.VERTICAL, command=self.txt_ana_res.yview)
        self.scy_ana_res.grid(row=2, column=1, sticky='ns', padx=(0,PAD), pady=PAD)
        self.txt_ana_res['yscrollcommand'] = self.scy_ana_res.set

        # Button close plots
        self.bt_ana_close_plots = ttk.Button(self.frm_ana, text='Close Plots', command=self.plots_close, width=15)
        self.bt_ana_close_plots.grid(row=3, column=0, columnspan=2)


    def widgets_analysis_prereg(self):
        self.frm_ana_prereg.rowconfigure([0], weight=1)
        self.frm_ana_prereg.columnconfigure([0], weight=1)

        # Analyze button
        self.bt_ana_prereg = ttk.Button(self.frm_ana_prereg, text='Analyze', command=self.analyze_prereg)
        self.bt_ana_prereg.grid(row=0, column=0)


    def widgets_analysis_explo1(self):
        self.frm_ana_explo1.rowconfigure([0,1,2,3,4,5,6], weight=1)
        self.frm_ana_explo1.columnconfigure([0,1], weight=1)

        ## Analysis Type
        self.lb_explo1_type = ttk.Label(self.frm_ana_explo1, text='Type')
        self.lb_explo1_type.grid(row=0, column=0, sticky='w', padx=PAD)

        self.cbb_explo1_type = ttk.Combobox(self.frm_ana_explo1, width=22)
        self.cbb_explo1_type.grid(row=0, column=1)
        self.cbb_explo1_type['values'] = ANA_TYPES
        self.cbb_explo1_type.state(['readonly'])
        self.cbb_explo1_type.set(ANA_TYPES[0])

        ## Options

        # Parallel channel
        self.var_explo1_pll = tk.BooleanVar(value=False)
        self.cb_explo1_pll = ttk.Checkbutton(self.frm_ana_explo1, text='Include parallel channel', variable=self.var_explo1_pll)
        self.cb_explo1_pll.grid(row=1, column=0, columnspan=2, sticky='w', padx=2*PAD)

        # Complementary p-value
        self.var_explo1_pcompl = tk.BooleanVar(value=False)
        self.cb_explo1_pcompl = ttk.Checkbutton(self.frm_ana_explo1, text='Complementary 1 - p', variable=self.var_explo1_pcompl)
        self.cb_explo1_pcompl.grid(row=2, column=0, columnspan=2, sticky='w', padx=2*PAD)

        # Exp 4
        self.var_explo1_exp4_invsel = tk.BooleanVar(value=False)
        self.cb_explo1_exp4_invsel = ttk.Checkbutton(self.frm_ana_explo1, text='Exp4: Invert byte selection', variable=self.var_explo1_exp4_invsel)
        self.cb_explo1_exp4_invsel.grid(row=3, column=0, columnspan=2, sticky='w', padx=2*PAD)

        ## Plots
        self.var_explo1_plot_pcum = tk.BooleanVar(value=False)
        self.cb_explo1_plot_pcum = ttk.Checkbutton(self.frm_ana_explo1, text='Plot: Cumulative p-values', variable=self.var_explo1_plot_pcum)
        self.cb_explo1_plot_pcum.grid(row=4, column=0, columnspan=2, sticky='w', padx=2*PAD)

        self.var_explo1_plot_pcum_ylog = tk.BooleanVar(value=False)
        self.cb_explo1_plot_pcum_ylog = ttk.Checkbutton(self.frm_ana_explo1, text='y-axis log scale', variable=self.var_explo1_plot_pcum_ylog)
        self.cb_explo1_plot_pcum_ylog.grid(row=5, column=0, columnspan=2, sticky='w', padx=6*PAD)

        ## Button
        self.bt_explo1 = ttk.Button(self.frm_ana_explo1, text='Analyze', command=self.analyze_explo, width=15)
        self.bt_explo1.grid(row=6, column=0, columnspan=2)


    def widgets_analysis_explo2(self):
        self.frm_ana_explo2.rowconfigure([0,1,2,3,4,5], weight=1)
        self.frm_ana_explo2.columnconfigure([0,1], weight=1)

        self.lb_explo2 = ttk.Label(self.frm_ana_explo2, text='Single session visualization')
        self.lb_explo2.grid(row=0, column=0, columnspan=2, sticky='w', padx=PAD)

        ## Analysis Type
        self.lb_explo2_type = ttk.Label(self.frm_ana_explo2, text='Type')
        self.lb_explo2_type.grid(row=1, column=0, sticky='w', padx=PAD)

        self.cbb_explo2_types = ['Auto', 'Bit Bias', 'Byte Bias']
        self.cbb_explo2_type = ttk.Combobox(self.frm_ana_explo2, width=22)
        self.cbb_explo2_type.grid(row=1, column=1)
        self.cbb_explo2_type['values'] = self.cbb_explo2_types
        self.cbb_explo2_type.state(['readonly'])
        self.cbb_explo2_type.set(self.cbb_explo2_types[0])

        ## Options

        # Parallel channel
        self.var_explo2_pll = tk.BooleanVar(value=False)
        self.cb_explo2_pll = ttk.Checkbutton(self.frm_ana_explo2, text='Include parallel channel', variable=self.var_explo2_pll)
        self.cb_explo2_pll.grid(row=2, column=0, columnspan=2, sticky='w', padx=2*PAD)

        # Exp 4
        self.var_explo2_exp4_invsel = tk.BooleanVar(value=False)
        self.cb_explo2_exp4_invsel = ttk.Checkbutton(self.frm_ana_explo2, text='Exp4: Invert byte selection', variable=self.var_explo2_exp4_invsel)
        self.cb_explo2_exp4_invsel.grid(row=3, column=0, columnspan=2, sticky='w', padx=2*PAD)

        # Feedb mag
        self.var_explo2_feedbmag = tk.BooleanVar(value=False)
        self.cb_explo2_feedbmag = ttk.Checkbutton(self.frm_ana_explo2, text='Show Feedback Magnitude', variable=self.var_explo2_feedbmag)
        self.cb_explo2_feedbmag.grid(row=4, column=0, columnspan=2, sticky='w', padx=2*PAD)

        ## Button
        self.bt_explo2 = ttk.Button(self.frm_ana_explo2, text='Plot', command=self.analyze_explo_singleplot, width=15)
        self.bt_explo2.grid(row=5, column=0, columnspan=2)


    def widgets_analysis_fsim(self):
        self.frm_ana_sim.rowconfigure([0,1,2,3,4,5], weight=1)
        self.frm_ana_sim.columnconfigure([0,1], weight=1)

        # Parameters
        self.lb_ana_sim_punif_nbins = ttk.Label(self.frm_ana_sim, text='Bins N')
        self.lb_ana_sim_punif_nbins.grid(row=0, column=0)

        self.var_ana_sim_punif_nbins = tk.IntVar(value=20)
        self.en_ana_sim_punif_nbins = ttk.Entry(self.frm_ana_sim, width=10, textvariable=self.var_ana_sim_punif_nbins, validate='key', validatecommand=self.validate_num_wrapper)
        self.en_ana_sim_punif_nbins.grid(row=0, column=1)

        self.lb_ana_sim_punif_ncomb = ttk.Label(self.frm_ana_sim, text='Comb N')
        self.lb_ana_sim_punif_ncomb.grid(row=1, column=0)

        self.var_ana_sim_punif_ncomb = tk.IntVar(value=60)
        self.en_ana_sim_punif_ncomb = ttk.Entry(self.frm_ana_sim, width=10, textvariable=self.var_ana_sim_punif_ncomb, validate='key', validatecommand=self.validate_num_wrapper)
        self.en_ana_sim_punif_ncomb.grid(row=1, column=1)

        self.var_ana_sim_puinf_plabels = tk.BooleanVar(value=True)
        self.cb_ana_sim_puinf_plabels = ttk.Checkbutton(self.frm_ana_sim, text='Show plot labels', variable=self.var_ana_sim_puinf_plabels)
        self.cb_ana_sim_puinf_plabels.grid(row=2, column=0, columnspan=2)

        # Analyze button
        self.bt_ana_sim_puinf = ttk.Button(self.frm_ana_sim, text='Uniformity p-values', command=self.analyze_fsim, width=20)
        self.bt_ana_sim_puinf.grid(row=3, column=0, columnspan=2)


    def db_search(self):
        file_in0 = self.var_db_file.get()
        file_dir_in0 = os.path.dirname(file_in0) if file_in0 else ''

        # DB select dialog
        db_file = tkfd.askopenfilename(parent=self, initialdir=file_dir_in0, filetypes=[('DB File', '.db')])
        if db_file is not None:
            self.var_db_file.set(db_file)


    def db_connect(self):
        db_file = self.var_db_file.get()
        if db_file is not None:
            conn_success = self.db.connect(db_file)

        if conn_success:
            # Clear filters
            self.filter_clear()

            # Update session data
            self.data_populate()

            # Save db_file to cfg file
            self.cfg.write('ANALYSIS', 'filename_db_last', db_file)


    def data_populate(self, tk_event=None):
        # get current filters
        filters = self.filter_get()

        # Clear all entries
        self.tree_data.delete(*self.tree_data.get_children())

        # Get sessions data
        data_n, data_values = self.db.sess_get_fields(VIEW_VARS, *filters, res_type='tuple')
        _, dict_data_values = self.db.sess_get_fields(VIEW_VARS, *filters, res_type='dol')

        # Insert table data
        for data in data_values:
            data = list(data)
            sess_hash = data[0]
            data[1] = str(data[1]).split('.')[0] # dt_start: Datetime to str
            self.tree_data.insert('', 'end', iid=sess_hash, values=data, tags=['data'])

        ## Update filter options
        if filters == (None, None, None, None):
            sess_groups = list(set(dict_data_values['sess_group']))
            sess_types = list(set(dict_data_values['sess_type']))
            sess_shams = list(set(dict_data_values['sess_sham']))
            part_ids = list(set(dict_data_values['part_id']))

            sess_groups.sort()
            sess_types.sort()
            sess_shams.sort()
            part_ids.sort()

            # Update Combobox widgets
            self.cbb_filt_sess_group['values'] = [''] + sess_groups
            self.cbb_filt_sess_type['values'] = [''] + sess_types
            self.cbb_filt_sess_sham['values'] = [''] + sess_shams
            self.cbb_filt_part_id['values'] = [''] + part_ids

            # Save number of entries
            self.data_n = data_n

        # Select all
        self.data_select_all()


    def data_selection_label(self, obj=None):
        filtered_n = len(self.tree_data.get_children())
        selected_n = len(self.tree_data.selection())
        self.lb_data_entries['text'] = self.data_entries_str.format(self.data_n, filtered_n, selected_n)


    def data_select_all(self):
        if self.data_selectall_toggle == False or len(self.tree_data.selection()) <= 1:
            # Select all
            self.data_selectall_toggle = True
            self.tree_data.selection_set(self.tree_data.get_children())
        else:
            # Select none
            self.data_selectall_toggle = False
            self.tree_data.selection_remove(self.tree_data.get_children())

        self.data_selection_label()


    def data_selected_ids(self):
        return self.tree_data.selection()


    def filter_get(self):
        sess_group = self.cbb_filt_sess_group.get()
        sess_type = self.cbb_filt_sess_type.get()
        sess_sham = self.cbb_filt_sess_sham.get()
        part_id = self.cbb_filt_part_id.get()

        sess_group = sess_group if sess_group != '' else None
        sess_type = sess_type if sess_type != '' else None
        part_id = part_id if part_id != '' else None

        if sess_sham == '':
            sess_sham = None
        elif sess_sham in ['True', 'true']:
            sess_sham = True
        else:
            sess_sham = False

        return sess_group, sess_type, sess_sham, part_id


    def filter_clear(self):
        self.cbb_filt_sess_group.set('')
        self.cbb_filt_sess_type.set('')
        self.cbb_filt_sess_sham.set('')
        self.cbb_filt_part_id.set('')

        self.data_populate()


    def analyze_show_result(self, res_str):
        self.txt_ana_res.insert('end', res_str)
        self.txt_ana_res.see('end')


    def analyze_prereg(self):
        # Retrieve the sess_hash of selected entries
        sess_hashes = self.data_selected_ids()

        if not len(sess_hashes):
            tkm.showerror(parent=self, title='Error', message='Select the experimental sessions to be analyzed')
            return

        # Get session's data
        sess_n, sessions_data = self.db.sess_get_data(sess_hashes, res_type='lod')
        _, sessions_data_dict = self.db.sess_get_data(sess_hashes, res_type='dol')

        sess_sham_n = sessions_data_dict['sess_sham'].count(True)
        sess_part_n = sess_n - sess_sham_n

        # More than 1 sess_type?
        sess_type_n = len(set(sessions_data_dict['sess_type']))
        if sess_type_n > 1:
            if not tkm.askyesno(parent=self, title='Warning', message='Filtering sessions by more than one sess_type. Proceed?'):
                return

        sess_types = ','.join(list(set(sessions_data_dict['sess_type'])))

        # Define analysis function
        ana_func = D_ANA_FUNCTIONS['Auto']
        exp4_invsel = False

        # Analyze sessions
        ps_part_tgt = np.zeros(sess_part_n, dtype=np.float64)
        ps_sham_tgt = np.zeros(sess_sham_n, dtype=np.float64)
        idx_part = 0
        idx_sham = 0

        for sess_data in sessions_data:
            sess_sham = sess_data['sess_sham']

            # Compute p-values; Ignore pll stream in prereg mode
            p_tgt, _ = ana_func(sess_data, exp4_invert_selection=exp4_invsel)

            # Assign to part or sham arrays
            if not sess_sham:
                ps_part_tgt[idx_part] = p_tgt
                idx_part += 1
            else:
                ps_sham_tgt[idx_sham] = p_tgt
                idx_sham += 1

        # Combine p-values via Fisher's Method
        if sess_part_n:
            p_part_tgt = fisher_combine(ps_part_tgt)

        if sess_sham_n:
            p_sham_tgt = fisher_combine(ps_sham_tgt)

        # Print results
        res_str = '=== {} Prereg Results'.format(sess_types)

        if sess_part_n:
            res_str += '\nPart sessions'
            res_str += '\n  tgt N={} p_x={:.8f}%'.format(len(ps_part_tgt), p_part_tgt*100)
        if sess_sham_n:
            res_str += '\nSham sessions'
            res_str += '\n  tgt N={} p_s={:.8f}%'.format(len(ps_sham_tgt), p_sham_tgt*100)
        if sess_part_n and sess_sham_n:
            exp_success = p_part_tgt <= 0.05 and p_sham_tgt > 0.05
            res_str += '\nExperiment Success: {}'.format(exp_success)

        res_str += '\n\n'

        print(res_str)
        self.analyze_show_result(res_str)


    def analyze_fsim(self):
        # Retrieve the sess_hash of selected entries
        sess_hashes = self.data_selected_ids()

        if not len(sess_hashes):
            tkm.showerror(parent=self, title='Error', message='Select the experimental sessions to be analyzed')
            return

        # Get parameters
        plot_punif_nbins = self.var_ana_sim_punif_nbins.get()
        plot_punif_ncomb = self.var_ana_sim_punif_ncomb.get()
        plot_labels = self.var_ana_sim_puinf_plabels.get()

        # Test parameters
        if plot_punif_nbins < 1:
            tkm.showerror(parent=self, title='Error', message='Provide a valid number of bins for the p-uniformity plot')
            return

        # Get session's data
        sess_n, sessions_data = self.db.sess_get_data(sess_hashes, res_type='lod')
        _, sessions_data_dict = self.db.sess_get_data(sess_hashes, res_type='dol')

        sess_sham_n = sessions_data_dict['sess_sham'].count(True)
        sess_part_n = sess_n - sess_sham_n

        # Any sham sess?
        if sess_sham_n > 0:
            tkm.showerror(parent=self, title='Error', message='Fast Simulation data is not supposed to contain sham sessions')
            return

        # More than 1 sess_type?
        sess_type_n = len(set(sessions_data_dict['sess_type']))
        if sess_type_n > 1:
            if not tkm.askyesno(parent=self, title='Warning', message='Filtering sessions by more than one sess_type. Proceed?'):
                return
        sess_type = list(set(sessions_data_dict['sess_type']))[0]

        # Define analysis function
        ana_func = D_ANA_FUNCTIONS['Auto']
        exp4_invsel = False

        # Analyze sessions
        ps_part_tgt = np.zeros(sess_part_n, dtype=np.float64)
        ps_part_pll = np.zeros(sess_part_n, dtype=np.float64)

        for i, sess_data in enumerate(sessions_data):
            # Compute p-values
            ps_part_tgt[i], ps_part_pll[i] = ana_func(sess_data, exp4_invert_selection=exp4_invsel)

        # Reshape p-values arrays
        if plot_punif_ncomb > 0:
            n_part_repeat = ps_part_tgt.size//plot_punif_ncomb
            ps_part_reshape_tgt = ps_part_tgt[:n_part_repeat*plot_punif_ncomb].reshape(n_part_repeat, plot_punif_ncomb)
            ps_part_reshape_pll = ps_part_pll[:n_part_repeat*plot_punif_ncomb].reshape(n_part_repeat, plot_punif_ncomb)

            # Combine p-values via Fisher's Method
            ps_part_tgt = np.zeros(n_part_repeat, dtype=np.float64)
            ps_part_pll = np.zeros(n_part_repeat, dtype=np.float64)
            for i in range(n_part_repeat):
                ps_part_tgt[i] = fisher_combine(ps_part_reshape_tgt[i])
                ps_part_pll[i] = fisher_combine(ps_part_reshape_pll[i])

        # Plot results
        f1, f2, chi2_tgt, p_chi2_tgt = plot_p_uniformity(ps_part_tgt, n_bins=plot_punif_nbins, fig_title=sess_type + ' tgt', plot_labels=plot_labels)
        f3, f4, chi2_pll, p_chi2_pll = plot_p_uniformity(ps_part_pll, n_bins=plot_punif_nbins, fig_title=sess_type + ' pll', plot_labels=plot_labels)

        self.plots.extend([f1, f2, f3, f4])

        # Print results
        res_str = '=== {} Fast Sim Results'.format(sess_type)
        res_str += '\n  tgt N={} chi2={:.2f} p_st={:.6f}%'.format(len(ps_part_tgt), chi2_tgt, p_chi2_tgt*100)
        res_str += '\n  pll N={} chi2={:.2f} p_sp={:.6f}%'.format(len(ps_part_pll), chi2_pll, p_chi2_pll*100)
        res_str += '\n\n'

        print(res_str)
        self.analyze_show_result(res_str)


    def analyze_explo(self):
        # Retrieve the sess_hash of selected entries
        sess_hashes = self.data_selected_ids()

        if not len(sess_hashes):
            tkm.showerror(parent=self, title='Error', message='Select the experimental sessions to be analyzed')
            return

        # Get analysis parameters
        ana_type = self.cbb_explo1_type.get()
        pll_chn = self.var_explo1_pll.get()
        p_compl = self.var_explo1_pcompl.get()
        exp4_invsel = self.var_explo1_exp4_invsel.get()
        plot_pcum = self.var_explo1_plot_pcum.get()
        plot_pcum_ylog = self.var_explo1_plot_pcum_ylog.get()

        # Get session's data
        sess_n, sessions_data = self.db.sess_get_data(sess_hashes, res_type='lod')
        _, sessions_data_dict = self.db.sess_get_data(sess_hashes, res_type='dol')

        sess_sham_n = sessions_data_dict['sess_sham'].count(True)
        sess_part_n = sess_n - sess_sham_n

        sess_types = ','.join(list(set(sessions_data_dict['sess_type'])))

        # Define analysis function
        ana_func = D_ANA_FUNCTIONS[ana_type]

        # Analyze sessions
        ps_part_tgt = np.zeros(sess_part_n, dtype=np.float64)
        ps_part_pll = np.zeros(sess_part_n, dtype=np.float64)
        ps_sham_tgt = np.zeros(sess_sham_n, dtype=np.float64)
        ps_sham_pll = np.zeros(sess_sham_n, dtype=np.float64)

        idx_part = 0
        idx_sham = 0

        if pll_chn:
            res_detailed_str = 'sess_hash, part_id, sess_type, sess_sham, p_tgt, p_pll'
        else:
            res_detailed_str = 'sess_hash, part_id, sess_type, sess_sham, p_tgt'

        for sess_data in sessions_data:
            sess_hash = sess_data['sess_hash']
            part_id = sess_data['part_id']
            sess_type = sess_data['sess_type']
            sess_sham = sess_data['sess_sham']
            sess_sham_txt = 'sham' if sess_sham else 'part'

            # Compute p-values
            p_tgt, p_pll = ana_func(sess_data, exp4_invert_selection=exp4_invsel)

            # Transform to complementary?
            if p_compl:
                p_tgt = 1. - p_tgt
                p_pll = 1. - p_pll

                # Correct for rare case when n0s==n1s
                if p_tgt == 0. :
                    p_tgt = 0.01
                if p_pll == 0. :
                    p_pll = 0.01

            # Assign to part or sham arrays
            if not sess_sham:
                ps_part_tgt[idx_part], ps_part_pll[idx_part] = p_tgt, p_pll
                idx_part += 1
            else:
                ps_sham_tgt[idx_sham], ps_sham_pll[idx_sham] = p_tgt, p_pll
                idx_sham += 1

            # Update detailed result text
            if pll_chn:
                res_detailed_str += '\n{}, {}, {}, {}, {:.8f}, {:.8f}'.format(sess_hash, part_id, sess_type, sess_sham_txt, p_tgt, p_pll)
            else:
                res_detailed_str += '\n{}, {}, {}, {}, {:.8f}'.format(sess_hash, part_id, sess_type, sess_sham_txt, p_tgt)

        res_detailed_str += '\n\n'

        # Combine p-values via Fisher's Method
        if sess_part_n:
            p_part_tgt = fisher_combine(ps_part_tgt)
            p_part_pll = fisher_combine(ps_part_pll)

            ps_part = np.hstack([ps_part_tgt, ps_part_pll])
            p_part = fisher_combine(ps_part)

        if sess_sham_n:
            p_sham_tgt = fisher_combine(ps_sham_tgt)
            p_sham_pll = fisher_combine(ps_sham_pll)

            ps_sham = np.hstack([ps_sham_tgt, ps_sham_pll])
            p_sham = fisher_combine(ps_sham)

        if sess_part_n and sess_sham_n:
            ps_controls = np.hstack([ps_part_pll, ps_sham_tgt, ps_sham_pll])
            p_controls = fisher_combine(ps_controls)

        # Print results
        res_str = '=== {} Explo Results'.format(sess_types)

        if sess_part_n:
            res_str += '\nPart sessions'
            res_str += '\n  tgt N={} p_xt={:.8f}%'.format(len(ps_part_tgt), p_part_tgt*100)
            if pll_chn:
                res_str += '\n  pll N={} p_xp={:.8f}%'.format(len(ps_part_pll), p_part_pll*100)
                res_str += '\n  tgt+pll N={} p_x={:.8f}%'.format(len(ps_part), p_part*100)
        if sess_sham_n:
            res_str += '\nSham sessions'
            res_str += '\n  tgt N={} p_st={:.8f}%'.format(len(ps_sham_tgt), p_sham_tgt*100)
            if pll_chn:
                res_str += '\n  pll N={} p_sp={:.8f}%'.format(len(ps_sham_pll), p_sham_pll*100)
                res_str += '\n  tgt+pll N={} p_s={:.8f}%'.format(len(ps_sham), p_sham*100)
        if sess_part_n and sess_sham_n:
            if pll_chn:
                res_str += '\nControl sessions'
                res_str += '\n  part tgt + sham tgt + sham pll'
                res_str += '\n  N={} p_c={:.8f}%'.format(len(ps_controls), p_controls*100)

        res_str += '\n\n'
        print(res_str)
        self.analyze_show_result(res_str)

        # Print results session by session
        print('=== {} Explo Results Detailed'.format(sess_types))
        print(res_detailed_str)

        # Plots
        if plot_pcum:
            if sess_part_n and sess_sham_n:
                if pll_chn:
                    f1 = plot_p_cumulative(ps_part_tgt, ps_part_pll, lbl_a='part tgt', lbl_b='part pll', yscale_log=plot_pcum_ylog)
                    f2 = plot_p_cumulative(ps_sham_tgt, ps_sham_pll, lbl_a='sham tgt', lbl_b='sham pll', yscale_log=plot_pcum_ylog)
                else:
                    f1 = plot_p_cumulative(ps_part_tgt, [], lbl_a='part tgt', lbl_b='', yscale_log=plot_pcum_ylog)
                    f2 = plot_p_cumulative(ps_sham_tgt, [], lbl_a='sham tgt', lbl_b='', yscale_log=plot_pcum_ylog)

                self.plots.extend([f1, f2])

            elif sess_part_n and not sess_sham_n:
                if pll_chn:
                    f1 = plot_p_cumulative(ps_part_tgt, ps_part_pll, lbl_a='part tgt', lbl_b='part pll', yscale_log=plot_pcum_ylog)
                else:
                    f1 = plot_p_cumulative(ps_part_tgt, [], lbl_a='part tgt', lbl_b='', yscale_log=plot_pcum_ylog)

                self.plots.append(f1)

            elif not sess_part_n and sess_sham_n:
                if pll_chn:
                    f1 = plot_p_cumulative(ps_sham_tgt, ps_sham_pll, lbl_a='sham tgt', lbl_b='sham pll', yscale_log=plot_pcum_ylog)
                else:
                    f1 = plot_p_cumulative(ps_sham_tgt, [], lbl_a='sham tgt', lbl_b='', yscale_log=plot_pcum_ylog)

                self.plots.append(f1)


    def analyze_explo_singleplot(self):
        # Retrieve the sess_hash of selected entries
        sess_hashes = self.data_selected_ids()

        if len(sess_hashes) != 1:
            tkm.showerror(parent=self, title='Error', message='Select a single session to be visualized')
            return

        # Get analysis parameters
        ana_type = self.cbb_explo2_type.get()
        pll_chn = self.var_explo2_pll.get()
        exp4_invsel = self.var_explo2_exp4_invsel.get()
        feedbmag = self.var_explo2_feedbmag.get()

        # Get session's data
        _, sessions_data = self.db.sess_get_data(sess_hashes, res_type='lod')
        session_data = sessions_data[0]

        ## Process data

        # Bytes
        rng_bytes_tgt, rng_bytes_pll = exps_bytes_definition(session_data, exp4_invert_selection=exp4_invsel)
        data_n = len(rng_bytes_tgt)

        # Define variable of interest
        if ana_type == 'Bit Bias':
            var_func = bit_bias_2tail_bytein
            var_label = 'Bit Bias'
        elif ana_type == 'Byte Bias':
            var_func = byte_bias_bytein
            var_label = 'Byte Bias'
        elif ana_type == 'Auto':
            sess_type = session_data['sess_type']
            if sess_type == 'EXP_3':
                var_func = byte_bias_bytein
                var_label = 'Byte Bias'
            else:
                var_func = bit_bias_2tail_bytein
                var_label = 'Bit Bias'

        # Calculate variables and p-values
        var_tgt = np.zeros(data_n, dtype=np.float64)
        var_pll = np.zeros(data_n, dtype=np.float64)
        p_tgt = np.zeros(data_n, dtype=np.float64)
        p_pll = np.zeros(data_n, dtype=np.float64)

        for i in range(data_n):
            bytes_tgt = rng_bytes_tgt[:i+1]
            bytes_pll = rng_bytes_pll[:i+1]

            var_tgt[i], p_tgt[i] = var_func(bytes_tgt)
            if pll_chn:
                var_pll[i], p_pll[i] = var_func(bytes_pll)

        # Convert p to feedback mag?
        if feedbmag:
            p_tgt = 1 - np.sqrt(p_tgt)
            p_pll = 1 - np.sqrt(p_pll)
            p_label = 'Feedback Mag'
        else:
            p_label = 'p-value'

        # X-axis, time in minutes
        frame_n = session_data['frame_n']
        frame_dur_ms = session_data['frame_dur_ms']
        sess_dur_min = frame_n * frame_dur_ms / 60000
        x_tmin = (np.arange(data_n) + 1)/data_n * sess_dur_min

        ## Plots
        f1 = plot_single_sess(x_tmin, var_tgt, p_tgt, title='Target Channel', lbl_var1=var_label, lbl_var2=p_label)
        self.plots.append(f1)

        if pll_chn:
            f2 = plot_single_sess(x_tmin, var_pll, p_pll, title='Parallel Channel', lbl_var1=var_label, lbl_var2=p_label)
            self.plots.append(f2)