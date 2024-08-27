"""
Copyright (c) 2024 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
Defines Experiment 3.
"""

import numpy as np

from anom_int_2024.experiments import EXP_BASE, EXP_CFG
from anom_int_2024.analysis import byte_bias


## EXP_3

class EXP_3(EXP_BASE):

    def __init__(self, rng, win_feedb):
        super().__init__('EXP_3', rng, win_feedb)

        # Exp Config
        self.cfg = EXP_CFG.copy()

        # Feedb vars
        self.bytes_hist = np.zeros(256, dtype=np.uint32)
        self.n_bytes = 0


    def feedb_pvalue(self, frame_i, exp_data_dict, bytes_array):
        # Update bytes histogram
        np.add.at(self.bytes_hist, bytes_array, 1) # self.bytes_hist[bytes_array] += 1 fails if len(bytes_array)>1 and some bytes are identical
        self.n_bytes += len(bytes_array)

        # Chisquare statistics
        _, p = byte_bias(self.bytes_hist, self.n_bytes)

        return p