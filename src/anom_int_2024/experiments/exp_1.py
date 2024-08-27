"""
Copyright (c) 2024 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
Defines Experiment 1.
"""

import numpy as np

from anom_int_2024.experiments import EXP_BASE, EXP_CFG
from anom_int_2024.analysis import popcount_lt, bit_bias_2tail


## EXP_1

class EXP_1(EXP_BASE):

    def __init__(self, rng, win_feedb):
        super().__init__('EXP_1', rng, win_feedb)

        # Exp Config
        self.cfg = EXP_CFG.copy()

        # Feedback vars
        self.n_1s = 0
        self.n_bits = 0


    def feedb_pvalue(self, frame_i, exp_data_dict, bytes_array):
        # Increment n_1s and n_bits
        self.n_1s += popcount_lt[bytes_array].sum()
        self.n_bits += 8*len(bytes_array)

        # Binomial statistics
        _, p = bit_bias_2tail(self.n_1s, self.n_bits)

        return p