# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "numpy>=1.20",
#   "pandas>=1.3",
#   "lifelines>=0.27",
# ]
# ///
"""Cox proportional hazards regression: fitting, summary, PH check."""

from typing import Dict, List, Optional
import numpy as np
import pandas as pd


def _prepare_cox_data(df: pd.DataFrame, time_col: str, event_col: str,
                      covariates: List[str], categorical_vars: List[str] = None,
                      reference_categories: Dict = None) -> pd.DataFrame:
    """Prepare DataFrame for Cox regression: select cols, encode categoricals, drop NaN."""
    categorical_vars = categorical_vars or []
    reference_categories = reference_categories or {}

    cols = [time_col, event_col] + covariates
    model_df = df[cols].copy()

    for cat_var in categorical_vars:
        if cat_var in model_df.columns:
            ref = reference_categories.get(cat_var)
            dummies = pd.get_dummies(model_df[cat_var], prefix=cat_var, drop_first=False)
            if ref:
                ref_col = f"{cat_var}_{ref}"
                if ref_col in dummies.columns:
                    dummies = dummies.drop(columns=[ref_col])
            else:
                dummies = dummies.iloc[:, 1:]
            model_df = model_df.drop(columns=[cat_var])
            model_df = pd.concat([model_df, dummies], axis=1)

    for col in model_df.columns:
        if col not in [time_col, event_col]:
            model_df[col] = pd.to_numeric(model_df[col], errors='coerce')

    model_df = model_df.dropna()
    return model_df


def fit_cox_univariate(df: pd.DataFrame, time_col: str, event_col: str,
                       covariate: str, display_name: str = None,
                       categorical_vars: List[str] = None,
                       reference_categories: Dict = None) -> List[Dict]:
    """Univariate Cox regression for a single covariate.

    Returns list of dicts (one per level for categoricals, one for continuous/binary).
    Each dict has: variable, hr, ci_lower, ci_upper, p_value, n, events.
    """
    from lifelines import CoxPHFitter

    categorical_vars = categorical_vars or []
    reference_categories = reference_categories or {}
    is_categorical = covariate in categorical_vars

    model_df = _prepare_cox_data(df, time_col, event_col, [covariate],
                                 categorical_vars=[covariate] if is_categorical else [],
                                 reference_categories=reference_categories)

    if len(model_df) < 10:
        return [{"variable": display_name or covariate,
                 "hr": np.nan, "ci_lower": np.nan, "ci_upper": np.nan,
                 "p_value": np.nan, "n": len(model_df),
                 "events": int(model_df[event_col].sum()),
                 "note": "Insufficient observations"}]

    try:
        cph = CoxPHFitter()
        cph.fit(model_df, duration_col=time_col, event_col=event_col)
        summary = cph.summary

        results = []
        for idx in summary.index:
            var_label = display_name or covariate
            if is_categorical:
                level = idx.replace(f"{covariate}_", "")
                ref = reference_categories.get(covariate, "ref")
                var_label = f"{display_name or covariate}: {level} vs {ref}"
            results.append({
                "variable": var_label,
                "hr": float(summary.loc[idx, 'exp(coef)']),
                "ci_lower": float(summary.loc[idx, 'exp(coef) lower 95%']),
                "ci_upper": float(summary.loc[idx, 'exp(coef) upper 95%']),
                "p_value": float(summary.loc[idx, 'p']),
                "n": len(model_df),
                "events": int(model_df[event_col].sum()),
            })
        return results
    except Exception as e:
        return [{"variable": display_name or covariate,
                 "hr": np.nan, "ci_lower": np.nan, "ci_upper": np.nan,
                 "p_value": np.nan, "n": len(model_df),
                 "events": int(model_df[event_col].sum()),
                 "note": f"Model failed: {str(e)}"}]


def fit_cox_multivariable(df: pd.DataFrame, time_col: str, event_col: str,
                          covariates: List[str], categorical_vars: List[str] = None,
                          reference_categories: Dict = None):
    """Fit multivariable Cox PH model. Returns (fitted CoxPHFitter, model_df)."""
    from lifelines import CoxPHFitter
    model_df = _prepare_cox_data(df, time_col, event_col, covariates,
                                 categorical_vars=categorical_vars,
                                 reference_categories=reference_categories)
    cph = CoxPHFitter()
    cph.fit(model_df, duration_col=time_col, event_col=event_col)
    return cph, model_df


def cox_summary_table(cph, rename: Dict = None) -> pd.DataFrame:
    """Extract Cox model summary as a clean DataFrame for reporting."""
    from datasci.pvalues import format_p_value
    rename = rename or {}
    s = cph.summary.copy()
    rows = []
    for idx in s.index:
        rows.append({
            "Variable": rename.get(idx, idx),
            "HR": f"{s.loc[idx, 'exp(coef)']:.2f}",
            "95% CI": f"({s.loc[idx, 'exp(coef) lower 95%']:.2f}–{s.loc[idx, 'exp(coef) upper 95%']:.2f})",
            "p-value": format_p_value(s.loc[idx, 'p']),
        })
    return pd.DataFrame(rows)


def check_proportional_hazards(cph, training_df=None) -> Dict:
    """Check PH assumption via Schoenfeld residuals test.

    Args:
        cph: Fitted CoxPHFitter
        training_df: The DataFrame used to fit (required by lifelines)
    """
    try:
        from lifelines.statistics import proportional_hazard_test
        test_results = proportional_hazard_test(cph, training_df, time_transform='rank')
        return {"summary": test_results.summary, "test_name": "Schoenfeld residuals test"}
    except Exception as e:
        return {"error": str(e), "test_name": "Schoenfeld residuals test"}
