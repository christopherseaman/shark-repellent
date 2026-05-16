import pandas as pd
import numpy as np

def test_chi_square_2x2_normal():
    from datasci.chisquare import perform_chi_square
    df = pd.DataFrame({
        "group": ["A"] * 50 + ["B"] * 50,
        "outcome": [1] * 40 + [0] * 10 + [0] * 40 + [1] * 10,
    })
    r = perform_chi_square(df, "group", "outcome")
    assert r["p_value"] < 0.001
    assert "chi-square" in r["method"]
    assert r["n"] == 100

def test_chi_square_2x2_with_zero_cell_falls_back_to_fisher():
    from datasci.chisquare import perform_chi_square
    df = pd.DataFrame({
        "group": ["A"] * 5 + ["B"] * 5,
        "outcome": [1] * 5 + [0] * 5,
    })
    r = perform_chi_square(df, "group", "outcome")
    assert r["method"] == "Fisher's exact"

def test_chi_square_rxc_table():
    from datasci.chisquare import perform_chi_square
    np.random.seed(0)
    df = pd.DataFrame({
        "x": np.random.choice(["a", "b", "c"], 200),
        "y": np.random.choice([1, 2, 3], 200),
    })
    r = perform_chi_square(df, "x", "y")
    assert "chi2_statistic" in r
    assert 0.0 <= r["p_value"] <= 1.0
