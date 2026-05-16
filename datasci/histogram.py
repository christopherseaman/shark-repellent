# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "numpy>=1.20",
#   "pandas>=1.3",
#   "matplotlib>=3.4",
# ]
# ///
"""Histogram with optional cutpoint annotation."""

from typing import Optional, Tuple
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd


def _count_at_cutpoint(data: pd.Series, cutpoint: float, operator: str) -> int:
    ops = {'<=': data <= cutpoint, '<': data < cutpoint,
           '>=': data >= cutpoint, '>': data > cutpoint}
    if operator not in ops:
        raise ValueError(f"Unknown operator '{operator}'; must be one of: <=, <, >=, >")
    return int(ops[operator].sum())


def create_histogram(data: pd.Series, title: str, xlabel: str,
                     bins: Optional[int] = None,
                     figsize: Optional[Tuple[float, float]] = None,
                     save_path: Optional[str] = None,
                     cutpoint: Optional[float] = None,
                     cutpoint_label: Optional[str] = None,
                     cutpoint_operator: Optional[str] = None,
                     dpi: int = 300) -> plt.Figure:
    """Create a standardized histogram with optional cutpoint annotation."""
    figsize = figsize or (8, 6)
    bins = bins or 20
    clean = data.dropna()
    fig, ax = plt.subplots(figsize=figsize)
    ax.hist(clean, bins=bins, alpha=0.7, color='skyblue', edgecolor='black')
    ax.set_xlabel(xlabel)
    ax.set_ylabel('Frequency')
    ax.set_title(title)
    ax.grid(True, alpha=0.3)

    if cutpoint is not None:
        op = cutpoint_operator or '<='
        ax.axvline(x=cutpoint, color='red', linestyle='--', linewidth=2, alpha=0.8)
        n_at_cut = _count_at_cutpoint(clean, cutpoint, op)
        label_text = cutpoint_label or f"Cutpoint: {cutpoint}"
        ax.text(cutpoint, ax.get_ylim()[1] * 0.95,
                f"  {label_text}\n  n={n_at_cut} ({n_at_cut/len(clean)*100:.1f}%)",
                color='red', fontsize=9, va='top')

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=dpi, bbox_inches='tight')
        plt.close(fig)
    return fig
