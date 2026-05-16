import pandas as pd

def test_summary_stats_basic():
    from datasci.summary import calculate_summary_stats
    s = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
    r = calculate_summary_stats(s)
    assert r["n"] == 5
    assert r["mean"] == 3.0
    assert r["median"] == 3.0
    assert r["min"] == 1.0
    assert r["max"] == 5.0
    assert r["q1"] == 2.0
    assert r["q3"] == 4.0
    assert r["iqr"] == 2.0
    assert r["n_missing"] == 0

def test_summary_stats_with_missing():
    from datasci.summary import calculate_summary_stats
    s = pd.Series([1.0, 2.0, None, 4.0])
    r = calculate_summary_stats(s)
    assert r["n"] == 3
    assert r["n_missing"] == 1

def test_summary_stats_no_quartiles():
    from datasci.summary import calculate_summary_stats
    s = pd.Series([1.0, 2.0, 3.0])
    r = calculate_summary_stats(s, include_quartiles=False)
    assert "q1" not in r
