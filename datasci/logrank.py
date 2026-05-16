# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "numpy>=1.20",
#   "pandas>=1.3",
#   "lifelines>=0.27",
# ]
# ///
"""Log-rank test for survival group comparison."""

from typing import Dict
import numpy as np
import pandas as pd


def perform_logrank(durations: pd.Series, event_observed: pd.Series,
                    group: pd.Series) -> Dict:
    """Log-rank test comparing groups."""
    from lifelines.statistics import logrank_test, multivariate_logrank_test

    mask = durations.notna() & event_observed.notna() & group.notna()
    dur = durations[mask]
    evt = event_observed[mask]
    grp = group[mask]

    unique_groups = sorted(grp.unique())
    if len(unique_groups) < 2:
        return {"test_statistic": np.nan, "p_value": np.nan,
                "note": f"Expected ≥2 groups, got {len(unique_groups)}"}

    if len(unique_groups) == 2:
        g1_mask = grp == unique_groups[0]
        result = logrank_test(
            dur[g1_mask], dur[~g1_mask],
            evt[g1_mask], evt[~g1_mask],
        )
    else:
        result = multivariate_logrank_test(dur, grp, evt)

    n_per_group = {str(g): int((grp == g).sum()) for g in unique_groups}
    return {
        "test_statistic": result.test_statistic,
        "p_value": result.p_value,
        "groups": list(unique_groups),
        "n_per_group": n_per_group,
    }
