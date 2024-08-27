"""
Copyright (c) 2024 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
Implements real-time feedback in the form of a circular display. The circle
features a gray dashed line indicating the p=30% reference, while the actual
value is represented in white and expands proportionally for higher feedback
magnitudes.
"""

import tkinter as tk
from tkinter import ttk


# PARAMETERS

CIRCLE_REF_WIDTH = 2
CIRCLE_REF_COLOR = 'gray'
CIRCLE_REF_DASH = 6

CIRCLE_FEEDB_WIDTH = 15
CIRCLE_FEEDB_COLOR = 'white'


# WIN_FEEDB_CIRCLE

class WIN_FEEDB_CIRCLE(tk.Toplevel):

    def __init__(self, parent):
        super().__init__(parent)
        self.title('Feedback')
        self.height = 315
        self.width = 315
        self.geometry('{}x{}'.format(self.height, self.width))
        self.protocol('WM_DELETE_WINDOW', lambda: None)
        self.parent = parent

        self.frame = ttk.Frame(self)
        self.frame.pack(fill=tk.BOTH, expand=tk.YES)

        self.canvas = tk.Canvas(self.frame, background='black', height=self.height, width=self.width, highlightthickness=0, borderwidth=0)
        self.canvas.bind("<Configure>", self.on_resize)
        self.canvas.pack(fill=tk.BOTH, expand=tk.YES)

        # Objects
        self.circle_ref = self.canvas.create_oval(0, 0, 0, 0, outline=CIRCLE_REF_COLOR, width=CIRCLE_REF_WIDTH, dash=CIRCLE_REF_DASH, tags='ref')
        self.circle_feedb = self.canvas.create_oval(0, 0, 0, 0, outline=CIRCLE_FEEDB_COLOR, width=CIRCLE_FEEDB_WIDTH, tags='feedb')

        # Start
        self.hide()


    def show(self):
        self.wm_deiconify()
        self.maximize()


    def hide(self):
        # Hide Feedback Circle
        if self.circle_feedb is not None:
            self.canvas.coords(self.circle_feedb, 0, 0, 0, 0)

        # Minimize
        self.withdraw()


    def minimize(self):
        self.iconify()


    def maximize(self):
        w = self.master.winfo_screenwidth()
        h = self.master.winfo_screenheight()
        self.geometry("%dx%d+0+0" % (w, h))


    def on_resize(self, event):
        self.width = event.width
        self.height = event.height

        # Resize canvas
        self.canvas.config(width=self.width, height=self.height)

        # Update reference
        self.draw_ref()


    def draw_ref(self):
        ORIG_WIN_SIZE = 315
        ORIG_CIRCLE_MAX_RADIUS = 150

        # Determine smaller size
        if self.width <=  self.height:
            scale = float(self.width) / ORIG_WIN_SIZE
        else:
            scale = float(self.height) / ORIG_WIN_SIZE

        # Find center, radius
        center_x = self.width / 2
        center_y = self.height / 2

        # Update p=30% reference
        feedb_mag_ref = 0.45228 # 1. - sqrt(.3)
        radius_ref = ORIG_CIRCLE_MAX_RADIUS * feedb_mag_ref * scale
        self.canvas.coords(self.circle_ref, center_x - radius_ref, center_y - radius_ref, center_x + radius_ref, center_y + radius_ref)


    def draw(self, diameter=0, color='white'):
        ORIG_WIN_SIZE = 315
        ORIG_CIRCLE_MAX_RADIUS = 150

        # Determine window smaller size
        if self.width <=  self.height:
            scale = float(self.width) / ORIG_WIN_SIZE
        else:
            scale = float(self.height) / ORIG_WIN_SIZE

        # Find center, radius
        center_x = self.width / 2
        center_y = self.height / 2
        radius = ORIG_CIRCLE_MAX_RADIUS * diameter * scale

        # Draw circle
        self.canvas.coords(self.circle_feedb, center_x - radius, center_y - radius, center_x + radius, center_y + radius)