import numpy as np
import pandas as pd

def test_logrank_two_groups():
    from datasci.logrank import perform_logrank
    rng = np.random.RandomState(0)
    n = 100
    dur = pd.Series(rng.exponential(scale=10, size=n*2))
    evt = pd.Series([1] * (n*2))
    grp = pd.Series([0] * n + [1] * n)
    r = perform_logrank(dur, evt, grp)
    assert "test_statistic" in r
    assert "p_value" in r
    assert r["groups"] == [0, 1]
    assert r["n_per_group"] == {"0": n, "1": n}

def test_logrank_single_group_handles_gracefully():
    from datasci.logrank import perform_logrank
    dur = pd.Series([1.0, 2.0, 3.0])
    evt = pd.Series([1, 1, 1])
    grp = pd.Series([0, 0, 0])
    r = perform_logrank(dur, evt, grp)
    assert "note" in r
