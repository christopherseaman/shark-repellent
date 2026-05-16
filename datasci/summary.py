# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pandas>=1.3",
# ]
# ///
"""Descriptive summary statistics for a single series."""

from typing import Dict
import pandas as pd


def calculate_summary_stats(data: pd.Series, include_quartiles: bool = True) -> Dict:
    """Calculate comprehensive summary statistics."""
    clean = data.dropna()
    result = {
        "n": len(clean), "n_missing": len(data) - len(clean),
        "mean": clean.mean(), "median": clean.median(),
        "std": clean.std(), "min": clean.min(), "max": clean.max(),
    }
    if include_quartiles:
        result.update({
            "q1": clean.quantile(0.25), "q3": clean.quantile(0.75),
            "iqr": clean.quantile(0.75) - clean.quantile(0.25),
        })
    return result
