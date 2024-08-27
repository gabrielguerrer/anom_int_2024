"""
Copyright (c) 2024 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
The Session Window becomes active during the data collection. It provides
information about the session's current stage and the remaining time until the
next step.
"""

import tkinter as tk
import tkinter.font as tkf
from tkinter import ttk

from anom_int_2024.experiments import TXT_SESS_DELAY, TXT_SESS_PREPARE, TXT_SESS_INTENTION

# PARAMETERS

PAD = 10


# WIN_SESSION

class WIN_SESSION(tk.Toplevel):

    def __init__(self, parent, exp_mgr):
        super().__init__(parent)
        self.title('Session Progress')
        self.geometry('390x270')
        self.resizable(False, False)
        self.protocol('WM_DELETE_WINDOW', lambda: None)
        self.rowconfigure([0], weight=1)
        self.columnconfigure([0], weight=1)
        self.parent = parent

        # Widgets
        self.widgets()

        # Experiment Manager
        self.exp_mgr = exp_mgr

        # Start
        self.tsk_wait = None
        self.hide()


    def show(self, sess_i=1, sess_n=1):
        self.title('Session Progress' + ('  {}/{}'.format(sess_i + 1, sess_n) if sess_n > 1 else ''))
        self.geometry('390x270+{}+{}'.format(self.parent.winfo_x() + self.parent.winfo_width() + 10, self.parent.winfo_y()))
        self.wm_deiconify()
        self.update()
        self.grab_set()         # Can't perform other actions while progress window is shown


    def hide(self):
        self.grab_release()
        self.withdraw()


    def widgets(self):
        self.frame = ttk.Frame(self, padding=(PAD, PAD))
        self.frame.grid(row=0, column=0, sticky='nsew')
        self.frame.columnconfigure([0,1], weight=1)
        self.frame.rowconfigure([0,1,2,3], weight=1)

        # Header
        self.var_header = tk.StringVar()
        self.lb_header = ttk.Label(self.frame, relief=tk.RIDGE, anchor='c', font=tkf.Font(size=12), textvariable=self.var_header)
        self.lb_header.grid(row=0, column=0, columnspan=2, sticky='ew', padx=PAD)

        # Instruction
        self.var_instruction = tk.StringVar()
        self.lb_instruction = ttk.Label(self.frame, anchor='c', font=tkf.Font(size=11), textvariable=self.var_instruction)
        self.lb_instruction.grid(row=1, column=0, columnspan=2, sticky='ew', padx=PAD)

        # Left
        self.var_left = tk.StringVar()
        self.lb_left = ttk.Label(self.frame, textvariable=self.var_left)
        self.lb_left.grid(row=2, column=0)

        # Right
        self.var_right = tk.StringVar()
        self.lb_right = ttk.Label(self.frame, font=tkf.Font(size=15), textvariable=self.var_right)
        self.lb_right.grid(row=2, column=1)

        # Cancel
        self.bt_cancel = ttk.Button(self.frame, text='Cancel', command=self.cancel_exp)
        self.bt_cancel.grid(row=3, column=0, columnspan=2)


    def cancel_exp(self):
        if self.tsk_wait is not None:
            self.after_cancel(self.tsk_wait)

        self.exp_mgr.exp_cancel()
        self.hide()


    def countdown(self, text_func, time_interval_min):
        text_func(time_interval_min)
        time_interval_min -= 1
        if time_interval_min > 0:
            self.tsk_wait = self.after(60000, self.countdown, text_func, time_interval_min)


    def text_delay(self, delay_min):
        self.var_header.set('Intervalo')
        self.var_instruction.set(TXT_SESS_DELAY)
        self.var_left.set('Tempo p/ início')
        self.var_right.set('{} min'.format(int(delay_min)))


    def text_prepare(self, time_left_min):
        self.var_header.set('Preparação')
        self.var_instruction.set(TXT_SESS_PREPARE)
        self.var_left.set('Tempo p/ início')
        self.var_right.set('{} min'.format(int(time_left_min)))


    def text_intention(self, time_left_min):
        self.var_header.set('Intenção')
        self.var_instruction.set(TXT_SESS_INTENTION)
        self.var_left.set('Tempo p/ fim')
        self.var_right.set('{} min'.format(int(time_left_min)))