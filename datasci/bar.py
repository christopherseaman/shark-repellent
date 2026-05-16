# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "numpy>=1.20",
#   "matplotlib>=3.4",
# ]
# ///
"""Standardized bar plot."""

from typing import List, Optional, Tuple
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def create_bar_plot(categories: List[str], values: List[float],
                    title: str, xlabel: str, ylabel: str,
                    figsize: Optional[Tuple[float, float]] = None,
                    save_path: Optional[str] = None,
                    dpi: int = 300) -> plt.Figure:
    """Create a standardized bar plot."""
    figsize = figsize or (8, 6)
    fig, ax = plt.subplots(figsize=figsize)
    x = np.arange(len(categories))
    ax.bar(x, values, alpha=0.7)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels(categories, rotation=45, ha='right')
    ax.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=dpi, bbox_inches='tight')
        plt.close(fig)
    return fig
