import os
import pandas as pd
from pathlib import Path

def test_create_markdown_section_with_heading():
    from datasci.report import create_markdown_section
    out = create_markdown_section("Test Heading")
    assert out.startswith("## Test Heading\n\n")

def test_create_markdown_section_with_dataframe():
    from datasci.report import create_markdown_section
    df = pd.DataFrame({"x": [1, 2], "y": [3, 4]})
    out = create_markdown_section("Data", table_data=df)
    assert "## Data" in out
    assert "|" in out  # markdown table pipes

def test_create_markdown_section_with_image():
    from datasci.report import create_markdown_section
    out = create_markdown_section("Plot", image_location="/some/path/plot.png")
    assert "![plot.png](media/plot.png)" in out

def test_format_statistical_results_uses_pvalues():
    from datasci.report import format_statistical_results
    out = format_statistical_results("My Test", {"p_value": 0.00001, "stat": 4.2})
    assert "< 0.0001" in out
    assert "stat: 4.200" in out

def test_generate_report_writes_file(tmp_path):
    from datasci.report import generate_report
    sections = [("Title", None, None), ("Other", {"k": "v"}, None)]
    out_path = tmp_path / "out.md"
    result_path = generate_report(sections, output_path=out_path)
    assert result_path.exists()
    content = result_path.read_text()
    assert "## Title" in out_path.read_text()
    assert "## Other" in content
