import pandas as pd


def test_cohens_d_large_effect():
    from datasci.effect_size import calculate_effect_size
    g1 = pd.Series([10.0, 11.0, 12.0, 13.0, 14.0])
    g2 = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
    r = calculate_effect_size(g1, g2)
    assert r["cohens_d"] > 0.8
    assert r["interpretation"] == "large"


def test_cohens_d_negligible():
    from datasci.effect_size import calculate_effect_size
    g1 = pd.Series([5.0, 5.1, 4.9, 5.0, 5.05])
    g2 = pd.Series([5.0, 5.1, 4.9, 5.0, 5.05])
    r = calculate_effect_size(g1, g2)
    assert abs(r["cohens_d"]) < 0.2
    assert r["interpretation"] == "negligible"
