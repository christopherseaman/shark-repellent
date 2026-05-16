# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pandas>=1.3",
# ]
# ///
"""p-value formatting and significance helpers."""

import pandas as pd


def is_significant(p_value: float, alpha: float) -> bool:
    return p_value < alpha


def format_p_value(p_value: float, precision: int = 4) -> str:
    if pd.isna(p_value):
        return "N/A"
    if p_value < 0.0001:
        return "< 0.0001"
    return f"{p_value:.{precision}f}"
