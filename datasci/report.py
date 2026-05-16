# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pandas>=1.3",
#   "tabulate>=0.9",  # required by pandas DataFrame.to_markdown() at runtime
# ]
# ///
"""Markdown report section/document builders."""

import os
import re
from pathlib import Path
import pandas as pd


def _ensure_table_spacing(text: str) -> str:
    """Ensure markdown tables have blank lines before and after them."""
    text = re.sub(
        r'(^[^|\n][^\n]*)\n(\|)',
        r'\1\n\n\2',
        text,
        flags=re.MULTILINE,
    )
    return text


def create_markdown_section(heading, table_data=None, image_location=None):
    """Create a markdown section with heading, optional table, optional image."""
    heading_level = 0
    heading_text = heading
    while heading_text.startswith('#'):
        heading_level += 1
        heading_text = heading_text[1:]
    if heading_level == 0:
        heading_level = 2

    section = f"{'#' * heading_level} {heading_text.strip()}\n\n"

    if table_data is not None:
        if isinstance(table_data, pd.DataFrame):
            section += table_data.to_markdown(index=False)
        elif isinstance(table_data, dict):
            if all(isinstance(v, (int, float, str)) for v in table_data.values()):
                df = pd.DataFrame({
                    'Variable': list(table_data.keys()),
                    'Value': list(table_data.values()),
                })
                section += df.to_markdown(index=False)
            else:
                for key, value in table_data.items():
                    section += f"**{key}**: {value}\n\n"
        else:
            section += _ensure_table_spacing(str(table_data))
        section += "\n\n"

    if image_location is not None:
        image_name = os.path.basename(image_location)
        section += f"![{image_name}](media/{image_name})\n\n"

    return section


def save_markdown_report(content, filename="report.md", output_dir="results"):
    """Save markdown content to a file under <cwd>/<output_dir>/<filename>."""
    output_path = Path.cwd() / output_dir / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(content)
    return output_path


def generate_report(report_sections, output_path=None):
    """Generate a markdown report from a list of (heading, table_data, image_location) tuples."""
    content = ""
    for heading, table_data, image_location in report_sections:
        content += create_markdown_section(heading, table_data, image_location)

    if output_path is None:
        output_path = Path.cwd() / "results" / "report.md"
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(content)
    return output_path


def format_statistical_results(test_name: str, results: dict) -> str:
    """Format statistical test results in a consistent markdown format."""
    from datasci.pvalues import format_p_value
    content = f"**{test_name}**\n\n"
    for key, value in results.items():
        if key == 'p_value':
            content += f"- {key}: {format_p_value(value)}\n"
        elif isinstance(value, float):
            content += f"- {key}: {value:.3f}\n"
        elif isinstance(value, dict):
            content += f"- {key}:\n"
            for sub_key, sub_value in value.items():
                if isinstance(sub_value, float):
                    content += f"  - {sub_key}: {sub_value:.3f}\n"
                else:
                    content += f"  - {sub_key}: {sub_value}\n"
        else:
            content += f"- {key}: {value}\n"
    return content
