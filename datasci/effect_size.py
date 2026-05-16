# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "numpy>=1.20",
#   "pandas>=1.3",
# ]
# ///
"""Cohen's d effect size."""

from typing import Dict
import numpy as np
import pandas as pd


def calculate_effect_size(group1: pd.Series, group2: pd.Series) -> Dict:
    """Calculate Cohen's d effect size."""
    n1, n2 = len(group1), len(group2)
    pooled_std = np.sqrt(((n1 - 1) * group1.var() + (n2 - 1) * group2.var()) / (n1 + n2 - 2))
    d = (group1.mean() - group2.mean()) / pooled_std
    abs_d = abs(d)
    if abs_d < 0.2:
        interp = "negligible"
    elif abs_d < 0.5:
        interp = "small"
    elif abs_d < 0.8:
        interp = "medium"
    else:
        interp = "large"
    return {"cohens_d": d, "interpretation": interp, "pooled_std": pooled_std}
