def test_consort_with_full_stats(tmp_path):
    from datasci.consort import plot_consort_flow
    stats = {
        "total_records": 500,
        "ineligible": 50,
        "eligible": 450,
        "excluded_missing_index_date": 10,
        "final_n": 440,
        "events": 200,
        "censored": 240,
        "ineligibility_reasons": {"reason A": 30, "reason B": 20},
    }
    out = tmp_path / "consort.png"
    plot_consort_flow(stats, save_path=str(out))
    assert out.exists()

def test_consort_no_missing_index_excluded(tmp_path):
    from datasci.consort import plot_consort_flow
    stats = {
        "total_records": 100, "ineligible": 0, "eligible": 100,
        "final_n": 100, "events": 50, "censored": 50,
    }
    out = tmp_path / "consort2.png"
    plot_consort_flow(stats, save_path=str(out))
    assert out.exists()
