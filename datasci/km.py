# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "numpy>=1.20",
#   "pandas>=1.3",
#   "matplotlib>=3.4",
#   "lifelines>=0.27",
# ]
# ///
"""Kaplan-Meier survival analysis: fitting + plotting + at-risk tables."""

from typing import Dict, List, Optional, Tuple
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd


def fit_km(durations: pd.Series, event_observed: pd.Series, label: str = None):
    """Fit a Kaplan-Meier estimator. Returns the fitted KaplanMeierFitter."""
    from lifelines import KaplanMeierFitter
    kmf = KaplanMeierFitter()
    mask = durations.notna() & event_observed.notna()
    kmf.fit(durations[mask], event_observed[mask], label=label)
    return kmf


def fit_km_by_group(df: pd.DataFrame, group_col: str, time_col: str,
                    event_col: str, group_labels: Dict = None,
                    min_n: int = 1) -> Dict:
    """Fit KM curves for each group in a column.

    Args:
        group_labels: Dict mapping raw values → display labels.
            If None, uses unique values as-is.
        min_n: Minimum group size to include.

    Returns dict mapping label → fitted KaplanMeierFitter.
    """
    if group_labels is None:
        group_labels = {g: str(g) for g in sorted(df[group_col].dropna().unique())}
    kmf_dict = {}
    for code, label in group_labels.items():
        mask = df[group_col] == code
        if mask.sum() >= min_n:
            kmf_dict[label] = fit_km(df.loc[mask, time_col],
                                     df.loc[mask, event_col], label=label)
    return kmf_dict


def km_at_timepoints(kmf, timepoints: List[int]) -> pd.DataFrame:
    """Extract KM estimates at specific timepoints.

    Returns DataFrame with columns: timepoint, survival, cumulative_incidence,
    ci_lower, ci_upper, n_at_risk, formatted.
    """
    rows = []
    for t in timepoints:
        s_t = float(kmf.predict(t))
        ci_1 = 1 - s_t

        ci_df = kmf.confidence_interval_survival_function_
        valid_idx = ci_df.index[ci_df.index <= t]
        if len(valid_idx) > 0:
            idx = valid_idx[-1]
            s_lower = float(ci_df.iloc[:, 0].loc[idx])
            s_upper = float(ci_df.iloc[:, 1].loc[idx])
            ci_ci_lower = 1 - s_upper
            ci_ci_upper = 1 - s_lower
        else:
            ci_ci_lower = 0.0
            ci_ci_upper = 0.0

        et = kmf.event_table
        at_risk_rows = et.index[et.index <= t]
        if len(at_risk_rows) > 0:
            last_t = at_risk_rows[-1]
            n_at_risk = int(et.loc[last_t, 'at_risk'] - et.loc[last_t, 'observed'] - et.loc[last_t, 'censored'])
        else:
            n_at_risk = int(et.iloc[0]['at_risk']) if len(et) > 0 else 0

        formatted = f"{ci_1 * 100:.1f}% ({ci_ci_lower * 100:.1f}–{ci_ci_upper * 100:.1f}%)"
        rows.append({
            "timepoint": t,
            "survival": s_t,
            "cumulative_incidence": ci_1,
            "ci_lower": ci_ci_lower,
            "ci_upper": ci_ci_upper,
            "n_at_risk": n_at_risk,
            "formatted": formatted,
        })
    return pd.DataFrame(rows)


def _resolve_colors(group_labels: List[str],
                    color_map: Optional[Dict[str, str]]) -> Dict[str, str]:
    """Build a color lookup from optional override + matplotlib Set1 fallback."""
    color_map = color_map or {}
    default_colors = plt.cm.Set1(np.linspace(0, 1, max(len(group_labels), 2)))
    resolved = {}
    for i, label in enumerate(group_labels):
        resolved[label] = color_map.get(label, default_colors[i])
    return resolved


def plot_km(kmf_dict: Dict, title: str,
            timepoints: List[int],
            p_value: Optional[float] = None,
            save_path: Optional[str] = None,
            show_ci: bool = True,
            xlabel: str = "Time",
            ylabel: str = "Survival Probability",
            invert: bool = False,
            xlim: Optional[Tuple[float, float]] = None,
            figsize: Tuple[float, float] = (8, 6),
            dpi: int = 300,
            color_map: Optional[Dict[str, str]] = None) -> plt.Figure:
    """Plot KM survival curves with a number-at-risk table.

    Args:
        kmf_dict: Dict mapping group label -> fitted KaplanMeierFitter
        title: Plot title
        timepoints: Landmark timepoints for at-risk table (required)
        p_value: Log-rank p-value to annotate
        save_path: Path to save figure
        show_ci: Show confidence intervals
        xlabel, ylabel: Axis labels
        invert: If True, plot 1-S(t) (cumulative incidence) instead of S(t)
        xlim: Optional (xmin, xmax). When set, at-risk table also filters to timepoints <= xmax.
        figsize, dpi: Matplotlib sizing
        color_map: Optional {label: color} override; falls back to Set1
    """
    from datasci.pvalues import format_p_value

    if xlim is not None:
        timepoints = [t for t in timepoints if t <= xlim[1]]
    group_labels = list(kmf_dict.keys())
    colors = _resolve_colors(group_labels, color_map)

    fig = plt.figure(figsize=figsize)
    gs = gridspec.GridSpec(2, 1, height_ratios=[4, 1], hspace=0.05)
    ax_main = fig.add_subplot(gs[0])
    ax_risk = fig.add_subplot(gs[1], sharex=ax_main)

    for label, kmf in kmf_dict.items():
        color = colors[label]
        times = kmf.survival_function_.index
        surv = kmf.survival_function_.values.flatten()
        y_vals = (1 - surv) if invert else surv

        ax_main.step(times, y_vals, where='post', color=color, linewidth=2, label=label)

        if show_ci:
            ci = kmf.confidence_interval_survival_function_
            ci_low = ci.iloc[:, 0].values
            ci_high = ci.iloc[:, 1].values
            if invert:
                ci_low, ci_high = 1 - ci_high, 1 - ci_low
            ax_main.fill_between(times, ci_low, ci_high, step='post',
                                 alpha=0.15, color=color)

    if p_value is not None:
        p_text = f"Log-rank p = {format_p_value(p_value)}"
        ax_main.text(0.98, 0.95, p_text, transform=ax_main.transAxes,
                     ha='right', va='top', fontsize=11,
                     bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    for t in timepoints:
        if t > 0:
            ax_main.axvline(x=t, color='gray', linestyle=':', alpha=0.3)

    ax_main.set_ylabel(ylabel)
    ax_main.set_xlabel(xlabel)
    ax_main.set_title(title)
    ax_main.set_ylim(bottom=0, top=1.05)
    if xlim is not None:
        ax_main.set_xlim(xlim)
    else:
        ax_main.set_xlim(left=0)
    ax_main.grid(True, alpha=0.3)
    ax_main.legend(loc='best')
    plt.setp(ax_main.get_xticklabels(), visible=False)

    ax_risk.axis('off')
    row_labels = list(kmf_dict.keys())
    cell_text = []
    for label, kmf in kmf_dict.items():
        et = kmf.event_table
        n_at_risk_row = []
        for t in timepoints:
            valid = et.index[et.index <= t]
            if len(valid) > 0:
                last_t = valid[-1]
                nar = int(et.loc[last_t, 'at_risk'] - et.loc[last_t, 'observed'] - et.loc[last_t, 'censored'])
                if t == 0:
                    nar = int(et.iloc[0]['at_risk'])
                n_at_risk_row.append(str(max(nar, 0)))
            else:
                n_at_risk_row.append(str(int(et.iloc[0]['at_risk'])))
        cell_text.append(n_at_risk_row)

    col_labels = [str(t) for t in timepoints]
    table = ax_risk.table(cellText=cell_text, rowLabels=row_labels,
                          colLabels=col_labels, loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.2)

    fig.subplots_adjust(left=0.1, right=0.95, top=0.92, bottom=0.08, hspace=0.05)
    if save_path:
        fig.savefig(save_path, dpi=dpi, bbox_inches='tight')
        plt.close(fig)
    return fig


def plot_loglog(kmf_dict: Dict, save_path: Optional[str] = None,
                title: str = "Log-Log Survival Plot (PH Check)",
                figsize: Tuple[float, float] = (8, 6),
                dpi: int = 300,
                color_map: Optional[Dict[str, str]] = None) -> plt.Figure:
    """Plot log(-log(S(t))) vs log(t) for proportional hazards visual check.

    Parallel lines suggest PH assumption holds.
    """
    group_labels = list(kmf_dict.keys())
    colors = _resolve_colors(group_labels, color_map)

    fig, ax = plt.subplots(figsize=figsize)

    for label, kmf in kmf_dict.items():
        color = colors[label]
        sf = kmf.survival_function_.copy()
        sf = sf[sf.iloc[:, 0] > 0]
        sf = sf[sf.index > 0]
        log_t = np.log(sf.index)
        log_neg_log_s = np.log(-np.log(sf.values.flatten()))
        ax.plot(log_t, log_neg_log_s, label=label, color=color, linewidth=2)

    ax.set_xlabel('log(time)')
    ax.set_ylabel('log(-log(S(t)))')
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    ax.legend()
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=dpi, bbox_inches='tight')
        plt.close(fig)
    return fig
