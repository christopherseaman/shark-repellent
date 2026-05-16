import numpy as np
import pandas as pd

def test_fit_km_returns_fitter():
    from datasci.km import fit_km
    rng = np.random.RandomState(0)
    dur = pd.Series(rng.exponential(scale=10, size=100))
    evt = pd.Series([1] * 100)
    kmf = fit_km(dur, evt, label="all")
    assert hasattr(kmf, "survival_function_")
    assert kmf.survival_function_.shape[0] > 0
    # label propagates to the survival_function_ column name
    assert "all" in str(kmf.survival_function_.columns[0])

def test_fit_km_by_group():
    from datasci.km import fit_km_by_group
    rng = np.random.RandomState(0)
    df = pd.DataFrame({
        "time": rng.exponential(scale=10, size=200),
        "event": [1] * 200,
        "grp": [0] * 100 + [1] * 100,
    })
    kmfs = fit_km_by_group(df, "grp", "time", "event")
    assert set(kmfs.keys()) == {"0", "1"}

def test_km_at_timepoints():
    from datasci.km import fit_km, km_at_timepoints
    rng = np.random.RandomState(0)
    dur = pd.Series(rng.exponential(scale=10, size=200))
    evt = pd.Series([1] * 200)
    kmf = fit_km(dur, evt)
    out = km_at_timepoints(kmf, [1, 5, 10])
    assert len(out) == 3
    assert "survival" in out.columns
    assert "cumulative_incidence" in out.columns

def test_plot_km_creates_png(tmp_path):
    from datasci.km import fit_km_by_group, plot_km
    rng = np.random.RandomState(0)
    df = pd.DataFrame({
        "time": rng.exponential(scale=10, size=200),
        "event": [1] * 200,
        "grp": [0] * 100 + [1] * 100,
    })
    kmfs = fit_km_by_group(df, "grp", "time", "event")
    out = tmp_path / "km.png"
    plot_km(kmfs, title="t", timepoints=[1, 5, 10], save_path=str(out))
    assert out.exists()
