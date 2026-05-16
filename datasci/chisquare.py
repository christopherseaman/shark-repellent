# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "numpy>=1.20",
#   "pandas>=1.3",
#   "scipy>=1.7",
# ]
# ///
"""Chi-square test of independence (with appropriate fallbacks)."""

from typing import Dict
import numpy as np
import pandas as pd
from scipy import stats as scipy_stats


def perform_chi_square(data: pd.DataFrame, col1: str, col2: str) -> Dict:
    """Test of association for categorical variables.

    2x2 tables: chi-square with Yates' correction (Fisher's exact if any cell is 0).
    r×c tables with expected < 5: Monte Carlo Fisher-Freeman-Halton simulation.
    Otherwise: chi-square test of independence.
    """
    contingency = pd.crosstab(data[col1], data[col2])
    n = contingency.sum().sum()
    ct = contingency.values
    chi2, _, dof, expected = scipy_stats.chi2_contingency(ct)

    if contingency.shape == (2, 2):
        if (ct == 0).any():
            _, p_val = scipy_stats.fisher_exact(ct)
            method = "Fisher's exact"
        else:
            chi2, p_val, dof, expected = scipy_stats.chi2_contingency(ct, correction=True)
            method = "chi-square (Yates')"
    elif (expected < 5).any():
        row_sums = ct.sum(axis=1)
        col_sums = ct.sum(axis=0)
        probs = np.outer(row_sums, col_sums).ravel() / n**2
        rng = np.random.default_rng(42)
        n_sim = 9999
        count = 0
        for _ in range(n_sim):
            sim = rng.multinomial(n, probs).reshape(ct.shape)
            try:
                if scipy_stats.chi2_contingency(sim)[0] >= chi2:
                    count += 1
            except ValueError:
                pass
        p_val = (count + 1) / (n_sim + 1)
        method = "Monte Carlo Fisher-Freeman-Halton"
    else:
        _, p_val, _, _ = scipy_stats.chi2_contingency(ct)
        method = "chi-square"

    min_dim = min(contingency.shape) - 1
    cramers_v = np.sqrt(chi2 / (n * min_dim)) if min_dim > 0 else 0
    return {
        "chi2_statistic": chi2, "p_value": p_val,
        "dof": dof, "cramers_v": cramers_v, "n": n,
        "contingency_table": contingency, "method": method,
    }
