# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "numpy>=1.20",
#   "pandas>=1.3",
#   "scipy>=1.7",
# ]
# ///
"""Fisher's exact test for 2x2 contingency tables."""

from typing import Dict
import numpy as np
import pandas as pd
from scipy import stats as scipy_stats


def fishers_exact_test(df: pd.DataFrame, var1: str, var2: str) -> Dict:
    """Fisher's exact test for 2x2 tables."""
    contingency = pd.crosstab(df[var1].dropna(), df[var2].dropna())
    if contingency.shape == (2, 2):
        odds_ratio, p_value = scipy_stats.fisher_exact(contingency)
        return {"odds_ratio": odds_ratio, "p_value": p_value, "contingency": contingency}
    return {"odds_ratio": np.nan, "p_value": np.nan, "note": "Not a 2x2 table"}
