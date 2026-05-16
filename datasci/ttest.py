# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "numpy>=1.20",
#   "pandas>=1.3",
#   "scipy>=1.7",
# ]
# ///
"""Two-sample t-test with mean-diff CI."""

from typing import Dict
import numpy as np
import pandas as pd
from scipy import stats as scipy_stats


def perform_t_test(group1: pd.Series, group2: pd.Series,
                   equal_var: bool = True) -> Dict[str, float]:
    """Perform t-test between two groups."""
    g1 = group1.dropna()
    g2 = group2.dropna()
    t_stat, p_val = scipy_stats.ttest_ind(g1, g2, equal_var=equal_var)
    mean_diff = g1.mean() - g2.mean()
    se_diff = np.sqrt(g1.var() / len(g1) + g2.var() / len(g2))
    ci_mult = scipy_stats.t.ppf(0.975, len(g1) + len(g2) - 2)
    return {
        "t_statistic": t_stat, "p_value": p_val,
        "mean_diff": mean_diff,
        "ci_lower": mean_diff - ci_mult * se_diff,
        "ci_upper": mean_diff + ci_mult * se_diff,
        "n_group1": len(g1), "n_group2": len(g2),
    }
