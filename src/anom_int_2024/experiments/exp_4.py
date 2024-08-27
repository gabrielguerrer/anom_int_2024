"""
Copyright (c) 2024 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
Defines Experiment 4.
"""

import numpy as np

from rng_rava import D_RNG_BIT_SRC
from anom_int_2024.experiments import EXP_BASE, EXP_4_CFG
from anom_int_2024.analysis import popcount_lt, bit_bias_2tail


## EXP_4

class EXP_4(EXP_BASE):

    def __init__(self, rng, win_feedb):
        super().__init__('EXP_4', rng, win_feedb)

        # Exp Config
        self.cfg = EXP_4_CFG.copy()

        # Feedb vars
        self.n_1s = 0
        self.n_bits = 0


    def initialize_extra(self, exp_data_dict):
        # Allocate byte subgroup indices
        frame_n = exp_data_dict['frame_n']
        exp_data_dict['rng_bytes_idx_a'] = np.zeros(frame_n, dtype=np.uint8)
        exp_data_dict['rng_bytes_idx_b'] = np.zeros(frame_n, dtype=np.uint8)


    def bytes_process(self, exp_data_dict, frame_i, bytes_a, bytes_b):
        # Generate byte subgroup indices
        idx_a, idx_b = self.rng.get_rng_bits(D_RNG_BIT_SRC['AB'])

        # Store the indices
        exp_data_dict['rng_bytes_idx_a'][frame_i] = idx_a
        exp_data_dict['rng_bytes_idx_b'][frame_i] = idx_b

        # Select bytes using the indices
        bytes_proc_a = bytes_a[[idx_a]]
        bytes_proc_b = bytes_b[[idx_b]]

        return bytes_proc_a, bytes_proc_b


    def feedb_pvalue(self, frame_i, exp_data_dict, bytes_array):
        # Increment n_1s and n_bits
        self.n_1s += popcount_lt[bytes_array].sum()
        self.n_bits += 8*len(bytes_array)

        # Binomial statistics
        _, p = bit_bias_2tail(self.n_1s, self.n_bits)

        return p