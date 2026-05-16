import pandas as pd

def test_t_test_obvious_difference():
    from datasci.ttest import perform_t_test
    g1 = pd.Series([10.0, 11.0, 12.0, 13.0, 14.0, 15.0])
    g2 = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    r = perform_t_test(g1, g2)
    assert r["p_value"] < 0.001
    assert r["mean_diff"] == 9.0
    assert r["n_group1"] == 6
    assert r["n_group2"] == 6
    assert r["ci_lower"] < r["ci_upper"]

def test_t_test_handles_nan():
    from datasci.ttest import perform_t_test
    g1 = pd.Series([1.0, 2.0, None, 4.0])
    g2 = pd.Series([5.0, 6.0, 7.0])
    r = perform_t_test(g1, g2)
    assert r["n_group1"] == 3
    assert r["n_group2"] == 3
