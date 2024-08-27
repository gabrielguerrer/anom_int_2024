"""
Copyright (c) 2024 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
Defines the statistical tools used for data collection and analysis.
"""

import numpy as np
from scipy.stats import binom, chi2, chisquare


# A linked table that tracks the number of 1s in all possible 256 byte values
popcount_lt = np.array([bin(i).count('1') for i in range(256)]).astype(np.uint8)


def bit_bias_1tail(n_1s, n_bits, tail_direction):
    # Bias
    bias = n_1s/n_bits - 0.5

    # Define onte-tail side
    if tail_direction in ['1', 1]:
        binom_area_fcn = binom.sf
    elif tail_direction in ['0', 0]:
        binom_area_fcn = binom.cdf
    else:
        return None, None

    # One-tailed p-value
    p = binom_area_fcn(n_1s-1, n=n_bits, p=0.5) # -1 leads to intervals (-inf, n_1) or [n_1, inf)

    return bias, p


def bit_bias_1tail_bytein(byte_array, tail_direction):
    n_1s = popcount_lt[byte_array].sum()
    n_bits = 8 * byte_array.size

    return bit_bias_1tail(n_1s, n_bits, tail_direction)


def bit_bias_2tail(n_1s, n_bits):
    # Bias
    bias = n_1s/n_bits - 0.5

    # Two-tailed p-value
    n_0s = n_bits - n_1s
    p_lo = binom.cdf(min(n_0s, n_1s)-1, n=n_bits, p=0.5) # (-inf, n_1s)
    p_hi = binom.sf(max(n_0s, n_1s)-1, n=n_bits, p=0.5)  # [n_1s, inf)
    p = p_lo + p_hi

    return bias, p


def bit_bias_2tail_bytein(byte_array):
    n_1s = popcount_lt[byte_array].sum()
    n_bits = 8 * byte_array.size

    return bit_bias_2tail(n_1s, n_bits)


def byte_bias(byte_hist, n_bytes):
    # Chisq p-value
    chisq, p = chisquare(byte_hist, n_bytes/256)

    ## Equivalent to
    # expect = n_bytes/256
    # chisq = 0
    # for y in byte_hist:
    #     chisq += (y - expect)**2 / expect
    # p = chi2.sf(chisq, 255)

    return chisq, p


def byte_bias_bytein(byte_array):
    byte_hist, _ = np.histogram(byte_array, 256, range=(0, 256))
    n_bytes = byte_array.size

    return byte_bias(byte_hist, n_bytes)


def fisher_combine(ps):
    # Fisher's method to combine p-values
    chisq = -2 * np.log(ps).sum()
    df = ps.size * 2
    p = chi2.sf(chisq, df)

    return p


def fisher_combine_cumulative(ps):
    # Cumulative combination. Each entry represents all previous p-values including the current one, combined using Fisher's method.
    n = ps.size
    ps_cumulative = np.zeros(n, dtype=np.float64)
    for i in range(n):
        ps_cumulative[i] = fisher_combine(ps[:i+1])

    return ps_cumulative