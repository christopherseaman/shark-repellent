def test_bar_plot_creates_png(tmp_path):
    from datasci.bar import create_bar_plot
    out = tmp_path / "bar.png"
    create_bar_plot(
        categories=["A", "B", "C"],
        values=[10.0, 20.0, 15.0],
        title="t", xlabel="cat", ylabel="val",
        save_path=str(out),
    )
    assert out.exists()
    assert out.stat().st_size > 500
