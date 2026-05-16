import pandas as pd
import numpy as np

def test_fisher_exact_2x2_obvious():
    from datasci.fisher import fishers_exact_test
    df = pd.DataFrame({
        "group": ["A"] * 10 + ["B"] * 10,
        "outcome": [1] * 9 + [0] * 1 + [0] * 9 + [1] * 1,
    })
    r = fishers_exact_test(df, "group", "outcome")
    assert r["p_value"] < 0.01
    assert not np.isnan(r["odds_ratio"])

def test_fisher_exact_non_2x2():
    from datasci.fisher import fishers_exact_test
    df = pd.DataFrame({
        "x": ["a", "b", "c", "a", "b", "c"],
        "y": [1, 0, 1, 0, 1, 0],
    })
    r = fishers_exact_test(df, "x", "y")
    assert np.isnan(r["p_value"])
    assert "note" in r
