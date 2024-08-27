"""
Copyright (c) 2024 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
Defines different methods for analyzing experimental sessions. The output
produces two p-values: one for the target and another for the parallel byte
channel.
"""

import numpy as np

from anom_int_2024.experiments import D_RES_P_TO_STARS
from anom_int_2024.analysis.ana_stats_tools import bit_bias_2tail_bytein, byte_bias_bytein


def exps_bytes_definition(exp_data, exp4_invert_selection=False):
    # Retrieve exp data
    rng_bytes_a = exp_data['rng_bytes_a']
    rng_bytes_b = exp_data['rng_bytes_b']
    feedb_rng_target = exp_data['feedb_rng_target']

    # Exp 4?
    if ('rng_bytes_idx_a' in exp_data) and ('rng_bytes_idx_b' in exp_data):
        # Retrieve byte selection indices
        rng_bytes_idx_a = exp_data['rng_bytes_idx_a']
        rng_bytes_idx_b = exp_data['rng_bytes_idx_b']

        # Has indices?
        if (rng_bytes_idx_a is not None) and (rng_bytes_idx_b is not None):

            # Invert selection pattern?
            if exp4_invert_selection:
                rng_bytes_idx_a = ~rng_bytes_idx_a & 1
                rng_bytes_idx_b = ~rng_bytes_idx_b & 1

            # Select bytes according to the indices
            rng_bytes_a = rng_bytes_a[np.arange(len(rng_bytes_idx_a)), rng_bytes_idx_a]
            rng_bytes_b = rng_bytes_b[np.arange(len(rng_bytes_idx_b)), rng_bytes_idx_b]

    # Defines target and parallel byte streams
    rng_bytes_tgt = rng_bytes_a if feedb_rng_target == 'A' else rng_bytes_b
    rng_bytes_pll = rng_bytes_b if feedb_rng_target == 'A' else rng_bytes_a

    # Flatten arrays
    rng_bytes_tgt = rng_bytes_tgt.flatten()
    rng_bytes_pll = rng_bytes_pll.flatten()

    return rng_bytes_tgt, rng_bytes_pll


def analyze_exp(exp_data, exp4_invert_selection=False):
    # Automatically detects the session type and assigns the corresponding analysis function
    sess_type = exp_data['sess_type']

    # Defines the analysis function according to the sess_type
    if sess_type == 'EXP_1':
        analyze_exp_func = analyze_exp_bit_bias_2tail

    elif sess_type == 'EXP_2':
        analyze_exp_func = analyze_exp_bit_bias_middleinvert_2tail

    elif sess_type == 'EXP_3':
        analyze_exp_func = analyze_exp_byte_bias

    elif sess_type == 'EXP_4':
        analyze_exp_func = analyze_exp_bit_bias_2tail

    return analyze_exp_func(exp_data, exp4_invert_selection=exp4_invert_selection)


def analyze_exp_bit_bias_2tail(exp_data, exp4_invert_selection=False):
    # Get target and parallel bytes
    rng_bytes_tgt, rng_bytes_pll = exps_bytes_definition(exp_data, exp4_invert_selection=exp4_invert_selection)

    # Binomial statistics
    _, p_tgt = bit_bias_2tail_bytein(rng_bytes_tgt)
    _, p_pll = bit_bias_2tail_bytein(rng_bytes_pll)

    return p_tgt, p_pll


def analyze_exp_bit_bias_middleinvert_2tail(exp_data, exp4_invert_selection=False):
    # Get target and parallel bytes
    rng_bytes_tgt, rng_bytes_pll = exps_bytes_definition(exp_data, exp4_invert_selection=exp4_invert_selection)

    # Slice byte samples in half
    rng_bytes_tgt_h1 = rng_bytes_tgt[:rng_bytes_tgt.size//2]
    rng_bytes_tgt_h2 = rng_bytes_tgt[rng_bytes_tgt.size//2:]
    rng_bytes_pll_h1 = rng_bytes_pll[:rng_bytes_pll.size//2]
    rng_bytes_pll_h2 = rng_bytes_pll[rng_bytes_pll.size//2:]

    # Invert the second half
    rng_bytes_inv_tgt = np.hstack([rng_bytes_tgt_h1, np.invert(rng_bytes_tgt_h2)])
    rng_bytes_inv_pll = np.hstack([rng_bytes_pll_h1, np.invert(rng_bytes_pll_h2)])

    # Binomial statistics
    _, p_tgt = bit_bias_2tail_bytein(rng_bytes_inv_tgt)
    _, p_pll = bit_bias_2tail_bytein(rng_bytes_inv_pll)

    return p_tgt, p_pll


def analyze_exp_byte_bias(exp_data, exp4_invert_selection=False):
    # Get target and parallel bytes
    rng_bytes_tgt, rng_bytes_pll = exps_bytes_definition(exp_data, exp4_invert_selection=exp4_invert_selection)

    # Chisquare statistics
    _, p_tgt = byte_bias_bytein(rng_bytes_tgt)
    _, p_pll = byte_bias_bytein(rng_bytes_pll)

    return p_tgt, p_pll


def calc_star_feedback(exp_data):
    # Calculate session target p-value
    p_tgt, _ = analyze_exp(exp_data)

    # Convert p into stars
    stars_p_range = np.array(list(D_RES_P_TO_STARS.keys()))
    n_stars = (p_tgt <= stars_p_range).sum()

    return int(n_stars)