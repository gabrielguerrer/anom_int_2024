"""
Copyright (c) 2024 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
The Feedback Star Window displays the participant's session outcome, represented
by a star-indexed rating that ranges from 1 to 3 stars.
"""

import tkinter as tk
import tkinter.font as tkf
from tkinter import ttk

from anom_int_2024.experiments import TXT_STAR_1, TXT_STAR_2, TXT_STAR_3


# PARAMETERS

PAD = 10


# WIN_FEEDB_STAR

class WIN_FEEDB_STAR(tk.Toplevel):

    def __init__(self, parent):
        super().__init__(parent)
        self.title('Session Result')
        self.geometry('390x270')
        self.protocol('WM_DELETE_WINDOW', lambda: None)
        self.resizable(False, False)
        self.rowconfigure([0], weight=1)
        self.columnconfigure([0], weight=1)
        self.parent = parent

        # Widgets
        self.widgets()

        # Start
        self.hide()


    def widgets(self):
        self.frame = ttk.Frame(self, padding=(PAD, PAD))
        self.frame.grid(row=0, column=0, sticky='nsew')
        self.frame.columnconfigure([0], weight=1)
        self.frame.rowconfigure([0,1,2,3], weight=1)

        # Stars
        self.var_stars = tk.StringVar()
        self.lb_stars = ttk.Label(self.frame, relief=tk.RIDGE, anchor='c', font=tkf.Font(size=40), textvariable=self.var_stars)
        self.lb_stars.grid(row=1, column=0, sticky='ew', padx=2*PAD)

        # Msg
        self.var_msg = tk.StringVar()
        self.lb_msg = ttk.Label(self.frame, textvariable=self.var_msg)
        self.lb_msg.grid(row=2, column=0, sticky='ew', padx=2*PAD)

        # Ok
        self.bt_ok = ttk.Button(self.frame, text='Ok', command=self.hide)
        self.bt_ok.grid(row=3, column=0)


    def show(self, n_stars):
        # Stars label
        self.var_stars.set(n_stars * u'\u2605')

        # Message
        if n_stars == 1:
            msg_txt = TXT_STAR_1
        elif n_stars == 2:
            msg_txt = TXT_STAR_2
        elif n_stars == 3:
            msg_txt = TXT_STAR_3
        else:
            msg_txt = ''

        self.var_msg.set(msg_txt)

        # Show window
        self.geometry('390x270+{}+{}'.format(self.parent.winfo_x() + self.parent.winfo_width() + 10, self.parent.winfo_y()))
        self.wm_deiconify()
        self.grab_set()         # Can't perform other actions while progress window is shown


    def hide(self):
        self.grab_release()
        self.withdraw()