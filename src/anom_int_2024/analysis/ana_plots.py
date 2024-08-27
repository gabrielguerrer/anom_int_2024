"""
Copyright (c) 2024 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
Defines different plots analysis for experimental sessions.

plot_p_cumulative(): Plots the p-values for each session and their cumulative
combination, where each point in the plot represents all previous values
including the current one, combined using Fisher's method.

plot_p_uniformity(): Calculates p-value homogeneity by binning the values and
conducting a chi-square test. Additionally, the p-values are sorted to
facilitate comparison between the empirical cumulative distribution function
and the expected linear distribution.

plot_single_sess(): Plots individual sessions, displaying the 5-minute
cumulative evolution of the variable of interest along with the associated
two-tailed p-value.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import binom, chisquare

from anom_int_2024.analysis import fisher_combine_cumulative

# PARAMETERS

P_CUM_MS = 3.5
P_UNIF_LW = 1.5
P_UNIF_MS = 1.5


# PLOTS

def plot_p_cumulative(ps_a, ps_b=[], lbl_a='', lbl_b='', yscale_log=False):
    # Process data
    n_a = len(ps_a)
    x_a = np.arange(1, n_a+1)

    n_b = len(ps_b)
    x_b = np.arange(1, n_b+1)

    if n_b == 0:
        ps_b = np.zeros(1)
        ps_b[0] = np.nan

    ps_cum_a = fisher_combine_cumulative(ps_a)
    ps_cum_b = fisher_combine_cumulative(ps_b)
    p_a = ps_cum_a[-1]
    p_b = ps_cum_b[-1]

    alpha = 0.05
    nsig_a = (ps_a <= alpha).sum()
    nsig_b = (ps_b <= alpha).sum()

    if yscale_log:
        p_max = 1.4
        p_min = np.nanmin(np.hstack([ps_a, ps_b, ps_cum_a, ps_cum_b]))
        p_min -= p_min*.2
        if p_min > .005:
            p_min = .005
    else:
        p_max = 1.05
        p_min = 0

    # Labels
    leg_p_a = 'p={:.4f}%'.format(p_a*100)
    leg_nsig_a = '<5% = {} ; {:.2f}%'.format(nsig_a, nsig_a/n_a*100)
    if n_b:
        leg_p_b = 'p={:.4f}%'.format(p_b*100)
        leg_nsig_b = '<5% = {} ; {:.2f}%'.format(nsig_b, nsig_b/n_b*100)
    else:
        leg_p_b = ''
        leg_nsig_b = ''

    # Colors
    if lbl_a.lower() == 'part tgt':
        col_a = 'royalblue'
    elif lbl_a.lower() == 'sham tgt':
        col_a = 'darkorange'
    elif lbl_a.lower() == 'part tgt+pll':
        col_a = 'goldenrod'
    elif lbl_a.lower() == 'ctrl':
        col_a = 'darkcyan'
    else:
        col_a = 'royalblue'

    if lbl_b.lower() == 'part pll':
        col_b = 'forestgreen'
    elif lbl_b.lower() == 'sham pll':
        col_b = 'darkviolet'
    elif lbl_b.lower() == 'sham tgt+pll':
        col_b = 'orchid'
    else:
        col_b = 'forestgreen'

    # Plot
    fig1, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, tight_layout=True, figsize=(10, 7), dpi=100)

    ax1.grid(axis='y')
    ax1.set_title(lbl_a)
    ax1.set_xlabel('Session')
    ax1.set_ylabel('p')
    if yscale_log:
        ax1.set_yscale('log')
    ax1.set_ylim(p_min, p_max)

    ax2.grid(axis='y')
    ax2.set_title(lbl_b)
    ax2.set_xlabel('Session')
    ax2.set_ylabel('p')
    if yscale_log:
        ax2.set_yscale('log')
    ax2.set_ylim(p_min, p_max)

    ax3.grid(axis='y')
    ax3.set_xlabel('Session')
    ax3.set_ylabel('p cumulative')
    if yscale_log:
        ax3.set_yscale('log')
    ax3.set_ylim(p_min, p_max)

    ax4.grid(axis='y')
    ax4.set_xlabel('Session')
    ax4.set_ylabel('p cumulative')
    if yscale_log:
        ax4.set_yscale('log')
    ax4.set_ylim(p_min, p_max)

    # Data A
    ax1.hlines(alpha, 1, n_a, color='black', ls='dashed', lw=1.)
    ax3.hlines(alpha, 1, n_a, color='black', ls='dashed', lw=1.)

    ax1.plot(x_a, ps_a, ls='none', marker='o', ms=P_CUM_MS, color=col_a, label=leg_nsig_a)
    ax3.plot(x_a, ps_cum_a, ls='none', marker='o', ms=P_CUM_MS, color=col_a, label=leg_p_a)

    ax1.legend(loc='upper right')
    ax3.legend(loc='upper right')

    # Data B
    if n_b:
        ax2.hlines(alpha, 1, n_b, color='black', ls='dashed', lw=1.)
        ax4.hlines(alpha, 1, n_b, color='black', ls='dashed', lw=1.)

        ax2.plot(x_b, ps_b, ls='none', marker='o', ms=P_CUM_MS, color=col_b, label=leg_nsig_b)
        ax4.plot(x_b, ps_cum_b, ls='none', marker='o', ms=P_CUM_MS, color=col_b, label=leg_p_b)

        ax2.legend(loc='upper right')
        ax4.legend(loc='upper right')

    fig1.show()

    return fig1


def plot_p_uniformity(ps, n_bins=10, fig_title='', plot_labels=True):
    # Process data
    n_sess = ps.size
    x_sort = (np.arange(n_sess)+1) / n_sess

    ys, bins = np.histogram(ps, n_bins, (0,1))
    chi2, p_chi2 = chisquare(ys, ps.size / n_bins)
    frac = np.sum(ps <= 0.05) / ps.size
    ps_sort = np.sort(ps)

    ci_95 = binom.interval(.95, n_sess, 1 / n_bins)

    # Labels
    label_chi2 = 'chi2={:.2f}, p={:.2f}%'.format(chi2, p_chi2*100)
    label_psig = 'p<5% = {:.2f}%'.format(frac*100)
    label_ci_95 = '95% CI'

    # Plot histrogram
    fig1, ax1 = plt.subplots(1, 1, tight_layout=True, figsize=(4, 3.75), dpi=100)

    ax1.set_xlabel('p\'')
    if plot_labels:
        ax1.set_title(fig_title)

    ax1.stairs(ys, bins, lw=P_UNIF_LW, color='black', label=label_chi2)
    ax1.hlines(ci_95, 0, 1, color='black', ls='dashed', lw=1, label=label_ci_95)
    if plot_labels:
        fig1.legend(loc='lower right', bbox_to_anchor=[.98, 0.2])

    fig1.show()

    # Plot CDF
    fig2, ax2 = plt.subplots(1, 1, tight_layout=True, figsize=(4, 3.75), dpi=100)

    ax2.set_ylabel('CDF')
    ax2.set_xlabel('p\'')
    if plot_labels:
        ax2.set_title(fig_title)

    ax2.plot(x_sort, ps_sort, color='black', marker='o', ls='none', ms=P_UNIF_MS, label=label_psig)
    ax2.plot([0, 1], [0, 1], color='black', lw=1)
    if plot_labels:
        fig2.legend(loc='lower right', bbox_to_anchor=[0.98, 0.2])

    fig2.show()

    return fig1, fig2, chi2, p_chi2


def plot_single_sess(x_var, y_var1, y_var2, title='', lbl_var1='', lbl_var2=''):
    RANGE_SKIP_FRAMES = 200

    # Plot
    fig, ax = plt.subplots(1, 1, tight_layout=True, figsize=(10, 4.5), dpi=100)

    ax.set_title(title)
    ax.set_xlabel('t (min)')
    ax.set_ylabel(lbl_var1)
    ax.yaxis.label.set_color('royalblue')
    ax.set_ylim(y_var1[RANGE_SKIP_FRAMES:].min()-0.005, y_var1[RANGE_SKIP_FRAMES:].max()+0.005)
    ax.grid(axis='y')

    ax_t = ax.twinx()
    ax_t.set_ylabel(lbl_var2)
    ax_t.yaxis.label.set_color('forestgreen')
    ax_t.set_ylim(-0.05, 1.05)

    ax.plot(x_var, y_var1, color='royalblue')
    ax_t.plot(x_var, y_var2, color='forestgreen')

    fig.show()

    return fig