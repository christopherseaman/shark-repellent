import pandas as pd
import numpy as np

def test_forest_plot_creates_png(tmp_path):
    from datasci.forest import plot_forest
    df = pd.DataFrame({
        "variable": ["age", "sex", "stage"],
        "hr": [1.05, 1.20, 2.50],
        "ci_lower": [1.01, 0.95, 1.50],
        "ci_upper": [1.10, 1.50, 4.00],
        "p_value": [0.01, 0.10, 0.001],
    })
    out = tmp_path / "forest.png"
    plot_forest(df, save_path=str(out))
    assert out.exists()

def test_forest_plot_handles_empty(tmp_path):
    from datasci.forest import plot_forest
    df = pd.DataFrame({"variable": [], "hr": [], "ci_lower": [], "ci_upper": [], "p_value": []})
    out = tmp_path / "forest_empty.png"
    plot_forest(df, save_path=str(out))
    assert out.exists()
