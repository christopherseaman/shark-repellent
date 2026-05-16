import numpy as np
import pandas as pd


def _toy_survival_df(n=200, seed=0):
    rng = np.random.RandomState(seed)
    age = rng.normal(60, 10, n)
    sex = rng.choice([0, 1], n)
    time = rng.exponential(scale=10, size=n)
    event = rng.choice([0, 1], n, p=[0.3, 0.7])
    return pd.DataFrame({"time": time, "event": event, "age": age, "sex": sex})


def test_fit_cox_univariate_continuous():
    from datasci.cox import fit_cox_univariate
    df = _toy_survival_df()
    out = fit_cox_univariate(df, "time", "event", "age")
    assert len(out) == 1
    assert "hr" in out[0]
    assert out[0]["n"] == len(df)


def test_fit_cox_multivariable_returns_fitter_and_data():
    from datasci.cox import fit_cox_multivariable
    df = _toy_survival_df()
    cph, model_df = fit_cox_multivariable(df, "time", "event", ["age", "sex"])
    assert hasattr(cph, "summary")
    assert len(model_df) == len(df)


def test_cox_summary_table_uses_pvalues_format():
    from datasci.cox import fit_cox_multivariable, cox_summary_table
    df = _toy_survival_df()
    cph, _ = fit_cox_multivariable(df, "time", "event", ["age"])
    t = cox_summary_table(cph)
    assert "Variable" in t.columns
    assert "HR" in t.columns
    assert "p-value" in t.columns


def test_check_proportional_hazards_returns_dict():
    from datasci.cox import fit_cox_multivariable, check_proportional_hazards
    df = _toy_survival_df()
    cph, model_df = fit_cox_multivariable(df, "time", "event", ["age", "sex"])
    r = check_proportional_hazards(cph, model_df)
    assert "test_name" in r
