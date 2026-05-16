# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "matplotlib>=3.4",
# ]
# ///
"""CONSORT-style patient exclusion flow diagram."""

from typing import Dict, Optional
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def plot_consort_flow(exclusion_stats: Dict,
                      save_path: Optional[str] = None,
                      title_total: str = "Total Records",
                      title_eligible: str = "Eligible cohort",
                      title_analytic: str = "Analytic cohort",
                      title_event: str = "Event observed",
                      title_censored: str = "Censored",
                      dpi: int = 300) -> plt.Figure:
    """Create a CONSORT-style patient exclusion flow diagram.

    `exclusion_stats` keys:
        total_records (int, required)
        ineligible (int, required)
        eligible (int, required)
        excluded_missing_index_date (int, optional — adds a second exclusion row)
        final_n (int, required)
        events (int, required)
        censored (int, required)
        ineligibility_reasons (Dict[str, int], optional — itemizes ineligible counts)
    """
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')

    box_props = dict(boxstyle='round,pad=0.4', facecolor='#e8f0fe', edgecolor='#333', linewidth=1.5)
    excl_props = dict(boxstyle='round,pad=0.4', facecolor='#fce8e8', edgecolor='#999', linewidth=1)
    arrow_props = dict(arrowstyle='->', color='#333', linewidth=1.5)

    total = exclusion_stats['total_records']
    ineligible = exclusion_stats['ineligible']
    eligible = exclusion_stats['eligible']
    excluded_index = exclusion_stats.get('excluded_missing_index_date', 0)
    final_n = exclusion_stats['final_n']
    events = exclusion_stats['events']
    censored = exclusion_stats['censored']
    reasons = exclusion_stats.get('ineligibility_reasons', {})

    cx = 3.5

    ax.text(cx, 9.2, f"{title_total}\nN = {total}", ha='center', va='center',
            fontsize=12, fontweight='bold', bbox=box_props)
    ax.annotate('', xy=(cx, 8.5), xytext=(cx, 8.8), arrowprops=arrow_props)

    ax.text(cx, 8.1, f"Assessed for eligibility\nN = {total}", ha='center', va='center',
            fontsize=11, bbox=box_props)
    ax.annotate('', xy=(cx, 7.1), xytext=(cx, 7.6), arrowprops=arrow_props)
    ax.annotate('', xy=(7, 7.8), xytext=(cx + 1.2, 7.8), arrowprops=arrow_props)

    reason_lines = [f"Ineligible (n = {ineligible})"]
    for reason, count in sorted(reasons.items(), key=lambda x: -x[1]):
        reason_lines.append(f"  • {reason}: {count}")
    ax.text(7.2, 7.8, "\n".join(reason_lines), ha='left', va='center',
            fontsize=9, bbox=excl_props)

    ax.text(cx, 6.7, f"{title_eligible}\nN = {eligible}", ha='center', va='center',
            fontsize=12, fontweight='bold', bbox=box_props)

    if excluded_index > 0:
        ax.annotate('', xy=(cx, 5.7), xytext=(cx, 6.2), arrowprops=arrow_props)
        ax.annotate('', xy=(7, 6.4), xytext=(cx + 1.2, 6.4), arrowprops=arrow_props)
        ax.text(7.2, 6.4, f"Excluded: missing index date\nn = {excluded_index}",
                ha='left', va='center', fontsize=9, bbox=excl_props)
        ax.text(cx, 5.3, f"{title_analytic}\nN = {final_n}", ha='center', va='center',
                fontsize=12, fontweight='bold', bbox=box_props)
        outcome_y = 4.3
        arrow_from = 4.8
    else:
        outcome_y = 5.3
        arrow_from = 6.2

    ax.annotate('', xy=(cx, outcome_y + 0.5), xytext=(cx, arrow_from), arrowprops=arrow_props)

    lx, rx = 1.8, 5.2
    ax.annotate('', xy=(lx, outcome_y - 0.2), xytext=(cx, outcome_y + 0.3), arrowprops=arrow_props)
    ax.annotate('', xy=(rx, outcome_y - 0.2), xytext=(cx, outcome_y + 0.3), arrowprops=arrow_props)

    event_props = dict(boxstyle='round,pad=0.4', facecolor='#e8fee8', edgecolor='#333', linewidth=1.5)
    censor_props = dict(boxstyle='round,pad=0.4', facecolor='#fff3e0', edgecolor='#333', linewidth=1.5)

    ax.text(lx, outcome_y - 0.7,
            f"{title_event}\nn = {events} ({events/final_n*100:.1f}%)",
            ha='center', va='center', fontsize=11, fontweight='bold', bbox=event_props)
    ax.text(rx, outcome_y - 0.7,
            f"{title_censored}\nn = {censored} ({censored/final_n*100:.1f}%)",
            ha='center', va='center', fontsize=11, fontweight='bold', bbox=censor_props)

    fig.suptitle("Patient Exclusion Flow", fontsize=14, fontweight='bold', y=0.98)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    if save_path:
        fig.savefig(save_path, dpi=dpi, bbox_inches='tight')
        plt.close(fig)
    return fig
