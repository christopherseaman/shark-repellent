# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "numpy>=1.20",
#   "pandas>=1.3",
#   "matplotlib>=3.4",
# ]
# ///
"""Forest plot for regression results."""

from typing import Optional
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def plot_forest(results_df: pd.DataFrame,
                save_path: Optional[str] = None,
                title: str = "Forest Plot — Hazard Ratios",
                effect_col: str = 'hr',
                effect_label: str = 'Hazard Ratio (95% CI)',
                forest_color: str = '#1f77b4',
                dpi: int = 300) -> plt.Figure:
    """Create a forest plot from regression results.

    Args:
        results_df: DataFrame with columns: variable, [effect_col], ci_lower, ci_upper, p_value
        save_path: Path to save figure
        title: Plot title
        effect_col: Column name for the effect estimate (default 'hr')
        effect_label: X-axis label
        forest_color: Marker/CI color
        dpi: Save DPI
    """
    df = results_df.dropna(subset=[effect_col]).copy()
    if len(df) == 0:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, 'No valid results for forest plot',
                ha='center', va='center', transform=ax.transAxes)
        if save_path:
            fig.savefig(save_path, dpi=dpi, bbox_inches='tight')
            plt.close(fig)
        return fig

    df = df.iloc[::-1]
    y_pos = np.arange(len(df))

    fig, ax = plt.subplots(figsize=(10, max(4, len(df) * 0.5 + 1)))

    has_ci = df['ci_lower'].notna() & df['ci_upper'].notna()
    df_ci = df[has_ci]
    df_no_ci = df[~has_ci]

    if len(df_ci) > 0:
        ci_positions = [list(df.index).index(i) for i in df_ci.index]
        ax.errorbar(df_ci[effect_col].values, ci_positions,
                    xerr=[df_ci[effect_col].values - df_ci['ci_lower'].values,
                          df_ci['ci_upper'].values - df_ci[effect_col].values],
                    fmt='o', color=forest_color, markersize=6, capsize=3, linewidth=1.5)

    if len(df_no_ci) > 0:
        no_ci_positions = [list(df.index).index(i) for i in df_no_ci.index]
        ax.plot(df_no_ci[effect_col].values, no_ci_positions,
                'D', color='#ff7f0e', markersize=6)

    ax.axvline(x=1.0, color='red', linestyle='--', alpha=0.7, linewidth=1)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(df['variable'])
    ax.set_xlabel(effect_label)
    ax.set_title(title)
    ax.grid(True, alpha=0.3, axis='x')

    for i, (idx, row) in enumerate(df.iterrows()):
        if pd.notna(row['ci_lower']) and pd.notna(row['ci_upper']):
            text = f"{row[effect_col]:.2f} ({row['ci_lower']:.2f}–{row['ci_upper']:.2f})"
        else:
            text = f"{row[effect_col]:.2f} (no CI)"
        ax.text(ax.get_xlim()[1] * 1.02, y_pos[i], text, va='center', fontsize=8)

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=dpi, bbox_inches='tight')
        plt.close(fig)
    return fig
