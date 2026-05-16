import os
from pathlib import Path

def test_diverging_bar_creates_png(tmp_path):
    from datasci.diverging_bar import create_diverging_bar_chart
    out = tmp_path / "chart.png"
    create_diverging_bar_chart(
        data={"Group A": [20.0, 30.0, 10.0, 25.0, 15.0],
              "Group B": [15.0, 25.0, 20.0, 20.0, 20.0]},
        labels=["SD", "D", "N", "A", "SA"],
        output_path=str(out),
        title="Smoke test",
    )
    assert out.exists()
    assert out.stat().st_size > 1000  # non-trivial PNG

def test_diverging_bar_rejects_empty_data():
    import pytest
    from datasci.diverging_bar import create_diverging_bar_chart
    with pytest.raises(ValueError):
        create_diverging_bar_chart(data={}, labels=["a"], output_path="ignored.png")
