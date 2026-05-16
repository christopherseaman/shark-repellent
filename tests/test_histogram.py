import pandas as pd
import numpy as np

def test_histogram_creates_png(tmp_path):
    from datasci.histogram import create_histogram
    out = tmp_path / "hist.png"
    s = pd.Series(np.random.RandomState(0).normal(size=200))
    create_histogram(s, title="Test", xlabel="Value", save_path=str(out))
    assert out.exists()
    assert out.stat().st_size > 500

def test_histogram_with_cutpoint(tmp_path):
    from datasci.histogram import create_histogram
    out = tmp_path / "hist2.png"
    s = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
    create_histogram(s, title="t", xlabel="x", save_path=str(out),
                     cutpoint=3.0, cutpoint_label="threshold", cutpoint_operator=">=")
    assert out.exists()
