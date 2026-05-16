# Shared-tools Restructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reorganize shark-repellent into a `curl | bash` installable toolset; integrate the 11ty static-site baseline and Python utilities from sibling repos (`../datasci_223`, `../ctsi-mao`).

**Architecture:** Six top-level units land in the repo: `datasci/` (Python utils, 15 single-purpose files with PEP 723 dep headers + lazy heavy imports), `11ty-base/` (static-site scaffolding), `notion-sync/` (unchanged), `firefox_autoconfig/` (unchanged), `cloudflare-worker/` (the `shark.badmath.org` Worker), and `install.sh` (bash dispatcher). The setuptools-era metadata at the repo root is deleted.

**Tech Stack:** Python 3.11+ with PEP 723 inline metadata; numpy/pandas/matplotlib/scipy/lifelines per-file; pytest (via `uv run --with`); Node + Eleventy 3.x; Bash; Cloudflare Worker (JavaScript) deployed via `wrangler`.

**Reference spec:** `docs/superpowers/specs/2026-05-15-shared-tools-restructure-design.md`

**Source repos (sibling paths):**
- `../ctsi-mao/utils/` — source for most datasci functions
- `../ctsi-mao/` (root) — source for 11ty-base files (`.eleventy.js`, `_includes/`, `css/`)
- `../datasci_223/` — secondary reference for 11ty baseline

---

## Conventions used throughout this plan

**Standard PEP 723 header** — every `datasci/*.py` file (except `__init__.py`) begins with this block, with `dependencies` matching the file's needs:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "<dep1>",
#   "<dep2>",
# ]
# ///
"""<one-line module docstring>."""
```

**Standard test invocation** — tests run via uv with deps `--with`-ed inline. To keep commands short, use the `tests/run.sh` script created in Task 0.1:

```bash
tests/run.sh tests/test_<name>.py -v
```

Under the hood that runs `uv run --with pytest --with numpy --with pandas --with matplotlib --with scipy --with lifelines pytest "$@"`.

**Commit messages** — conventional commits, no co-authored-by (per repo conventions in CLAUDE.md). Example: `feat(datasci): extract ttest from ctsi-mao`.

**Lazy imports** — for heavy deps (`lifelines`, anything not in the basic numpy/pandas/matplotlib/scipy set), put the `import` inside the function body, not at module top:

```python
def fit_km(...):
    from lifelines import KaplanMeierFitter
    ...
```

This means `import datasci.km` does not force `lifelines` to be installed.

---

# Phase 0: Test infrastructure

## Task 0.1: Create test runner script

**Files:**
- Create: `tests/run.sh`
- Create: `tests/__init__.py` (empty, so pytest can collect)
- Create: `.gitignore` updates (add `.pytest_cache/`, already excluded — verify)

- [ ] **Step 1: Verify pytest cache already excluded**

Run: `grep -n "pytest_cache" .gitignore`
Expected: line `.pytest_cache/` is present.

- [ ] **Step 2: Create `tests/__init__.py`**

```bash
mkdir -p tests
touch tests/__init__.py
```

- [ ] **Step 3: Create `tests/run.sh`**

Write to `tests/run.sh`:

```bash
#!/usr/bin/env bash
# Test runner: wraps `uv run pytest` with the union of deps needed across
# all datasci modules. Pass through any pytest args ($@), e.g.:
#   tests/run.sh tests/test_ttest.py -v
set -euo pipefail
export MPLBACKEND=Agg   # avoid matplotlib trying to open a display
exec uv run \
  --with pytest \
  --with numpy \
  --with pandas \
  --with matplotlib \
  --with scipy \
  --with lifelines \
  --with tabulate \
  pytest "$@"
```

`chmod +x tests/run.sh`.

`tabulate` is required by pandas' `DataFrame.to_markdown()` which `report.py` uses.

- [ ] **Step 4: Verify it runs (no tests yet)**

Run: `tests/run.sh tests/ -v`
Expected: exits 0 or 5 (no tests collected — both are acceptable here).

- [ ] **Step 5: Commit**

```bash
git add tests/run.sh tests/__init__.py
git commit -m "chore: add pytest runner via uv with inline deps"
```

---

# Phase 1: Extract Python utilities into `datasci/`

The directory `viztools/` currently exists (with `charts.py` and `__init__.py`). We will:
1. Create `datasci/` as the new home.
2. Move/extract files into it one at a time, each with its own pytest smoke test.
3. Delete `viztools/` once `diverging_bar.py` is migrated.

Files written in order of dependency: simplest primitives first, then files that depend on them. Within `datasci/`, the only intra-package imports are `report.py → pvalues.py` and `km.py → pvalues.py` (see spec). Build `pvalues.py` first so the others can reference it.

## Task 1.1: Create `datasci/__init__.py`

**Files:**
- Create: `datasci/__init__.py` (empty)

- [ ] **Step 1: Create the package marker**

```bash
mkdir -p datasci
touch datasci/__init__.py
```

- [ ] **Step 2: Verify package shape**

Run: `python -c "import datasci; print(datasci.__file__)"`
Expected: prints the path `.../datasci/__init__.py`. (No `uv` needed — empty module has no deps.)

- [ ] **Step 3: Commit**

```bash
git add datasci/__init__.py
git commit -m "feat(datasci): create empty package marker"
```

---

## Task 1.2: `datasci/pvalues.py` — `format_p_value`, `is_significant`

**Files:**
- Create: `datasci/pvalues.py`
- Create: `tests/test_pvalues.py`

**Source:** `../ctsi-mao/utils/stats_utils.py` lines 97–106.

- [ ] **Step 1: Write failing test**

Write to `tests/test_pvalues.py`:

```python
import math

def test_format_p_value_small():
    from datasci.pvalues import format_p_value
    assert format_p_value(0.00001) == "< 0.0001"

def test_format_p_value_normal():
    from datasci.pvalues import format_p_value
    assert format_p_value(0.0234) == "0.0234"

def test_format_p_value_nan():
    from datasci.pvalues import format_p_value
    assert format_p_value(float("nan")) == "N/A"

def test_is_significant_true():
    from datasci.pvalues import is_significant
    assert is_significant(0.01, 0.05) is True

def test_is_significant_false():
    from datasci.pvalues import is_significant
    assert is_significant(0.10, 0.05) is False
```

- [ ] **Step 2: Run to verify failure**

Run: `tests/run.sh tests/test_pvalues.py -v`
Expected: ImportError / ModuleNotFoundError on `datasci.pvalues`.

- [ ] **Step 3: Implement**

Write to `datasci/pvalues.py`:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pandas>=1.3",
# ]
# ///
"""p-value formatting and significance helpers."""

import pandas as pd


def is_significant(p_value: float, alpha: float) -> bool:
    return p_value < alpha


def format_p_value(p_value: float, precision: int = 4) -> str:
    if pd.isna(p_value):
        return "N/A"
    if p_value < 0.0001:
        return "< 0.0001"
    return f"{p_value:.{precision}f}"
```

- [ ] **Step 4: Run to verify pass**

Run: `tests/run.sh tests/test_pvalues.py -v`
Expected: all 5 tests pass.

- [ ] **Step 5: Commit**

```bash
git add datasci/pvalues.py tests/test_pvalues.py
git commit -m "feat(datasci): add pvalues (format_p_value, is_significant)"
```

---

## Task 1.3: `datasci/summary.py` — `calculate_summary_stats`

**Files:**
- Create: `datasci/summary.py`
- Create: `tests/test_summary.py`

**Source:** `../ctsi-mao/utils/stats_utils.py` lines 81–94.

- [ ] **Step 1: Write failing test**

Write to `tests/test_summary.py`:

```python
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
```

- [ ] **Step 2: Run to verify failure**

Run: `tests/run.sh tests/test_summary.py -v`
Expected: ImportError on `datasci.summary`.

- [ ] **Step 3: Implement**

Write to `datasci/summary.py`:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pandas>=1.3",
# ]
# ///
"""Descriptive summary statistics for a single series."""

from typing import Dict
import pandas as pd


def calculate_summary_stats(data: pd.Series, include_quartiles: bool = True) -> Dict:
    """Calculate comprehensive summary statistics."""
    clean = data.dropna()
    result = {
        "n": len(clean), "n_missing": len(data) - len(clean),
        "mean": clean.mean(), "median": clean.median(),
        "std": clean.std(), "min": clean.min(), "max": clean.max(),
    }
    if include_quartiles:
        result.update({
            "q1": clean.quantile(0.25), "q3": clean.quantile(0.75),
            "iqr": clean.quantile(0.75) - clean.quantile(0.25),
        })
    return result
```

- [ ] **Step 4: Run to verify pass**

Run: `tests/run.sh tests/test_summary.py -v`
Expected: all 3 tests pass.

- [ ] **Step 5: Commit**

```bash
git add datasci/summary.py tests/test_summary.py
git commit -m "feat(datasci): add summary stats"
```

---

## Task 1.4: `datasci/effect_size.py` — `calculate_effect_size`

**Files:**
- Create: `datasci/effect_size.py`
- Create: `tests/test_effect_size.py`

**Source:** `../ctsi-mao/utils/stats_utils.py` lines 109–123.

- [ ] **Step 1: Write failing test**

Write to `tests/test_effect_size.py`:

```python
import pandas as pd

def test_cohens_d_large_effect():
    from datasci.effect_size import calculate_effect_size
    g1 = pd.Series([10.0, 11.0, 12.0, 13.0, 14.0])
    g2 = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
    r = calculate_effect_size(g1, g2)
    assert r["cohens_d"] > 0.8
    assert r["interpretation"] == "large"

def test_cohens_d_negligible():
    from datasci.effect_size import calculate_effect_size
    g1 = pd.Series([5.0, 5.1, 4.9, 5.0, 5.05])
    g2 = pd.Series([5.0, 5.1, 4.9, 5.0, 5.05])
    r = calculate_effect_size(g1, g2)
    assert abs(r["cohens_d"]) < 0.2
    assert r["interpretation"] == "negligible"
```

- [ ] **Step 2: Run to verify failure**

Run: `tests/run.sh tests/test_effect_size.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement**

Write to `datasci/effect_size.py`:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "numpy>=1.20",
#   "pandas>=1.3",
# ]
# ///
"""Cohen's d effect size."""

from typing import Dict
import numpy as np
import pandas as pd


def calculate_effect_size(group1: pd.Series, group2: pd.Series) -> Dict:
    """Calculate Cohen's d effect size."""
    n1, n2 = len(group1), len(group2)
    pooled_std = np.sqrt(((n1 - 1) * group1.var() + (n2 - 1) * group2.var()) / (n1 + n2 - 2))
    d = (group1.mean() - group2.mean()) / pooled_std
    abs_d = abs(d)
    if abs_d < 0.2:
        interp = "negligible"
    elif abs_d < 0.5:
        interp = "small"
    elif abs_d < 0.8:
        interp = "medium"
    else:
        interp = "large"
    return {"cohens_d": d, "interpretation": interp, "pooled_std": pooled_std}
```

- [ ] **Step 4: Run to verify pass**

Run: `tests/run.sh tests/test_effect_size.py -v`
Expected: both tests pass.

- [ ] **Step 5: Commit**

```bash
git add datasci/effect_size.py tests/test_effect_size.py
git commit -m "feat(datasci): add Cohen's d effect size"
```

---

## Task 1.5: `datasci/ttest.py` — `perform_t_test`

**Files:**
- Create: `datasci/ttest.py`
- Create: `tests/test_ttest.py`

**Source:** `../ctsi-mao/utils/stats_utils.py` lines 15–30.

- [ ] **Step 1: Write failing test**

Write to `tests/test_ttest.py`:

```python
import pandas as pd

def test_t_test_obvious_difference():
    from datasci.ttest import perform_t_test
    g1 = pd.Series([10.0, 11.0, 12.0, 13.0, 14.0, 15.0])
    g2 = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    r = perform_t_test(g1, g2)
    assert r["p_value"] < 0.001
    assert r["mean_diff"] == 9.0
    assert r["n_group1"] == 6
    assert r["n_group2"] == 6
    assert r["ci_lower"] < r["ci_upper"]

def test_t_test_handles_nan():
    from datasci.ttest import perform_t_test
    g1 = pd.Series([1.0, 2.0, None, 4.0])
    g2 = pd.Series([5.0, 6.0, 7.0])
    r = perform_t_test(g1, g2)
    assert r["n_group1"] == 3
    assert r["n_group2"] == 3
```

- [ ] **Step 2: Run to verify failure**

Run: `tests/run.sh tests/test_ttest.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement**

Write to `datasci/ttest.py`:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "numpy>=1.20",
#   "pandas>=1.3",
#   "scipy>=1.7",
# ]
# ///
"""Two-sample t-test with mean-diff CI."""

from typing import Dict
import numpy as np
import pandas as pd
from scipy import stats as scipy_stats


def perform_t_test(group1: pd.Series, group2: pd.Series,
                   equal_var: bool = True) -> Dict[str, float]:
    """Perform t-test between two groups."""
    g1 = group1.dropna()
    g2 = group2.dropna()
    t_stat, p_val = scipy_stats.ttest_ind(g1, g2, equal_var=equal_var)
    mean_diff = g1.mean() - g2.mean()
    se_diff = np.sqrt(g1.var() / len(g1) + g2.var() / len(g2))
    ci_mult = scipy_stats.t.ppf(0.975, len(g1) + len(g2) - 2)
    return {
        "t_statistic": t_stat, "p_value": p_val,
        "mean_diff": mean_diff,
        "ci_lower": mean_diff - ci_mult * se_diff,
        "ci_upper": mean_diff + ci_mult * se_diff,
        "n_group1": len(g1), "n_group2": len(g2),
    }
```

- [ ] **Step 4: Run to verify pass**

Run: `tests/run.sh tests/test_ttest.py -v`
Expected: both tests pass.

- [ ] **Step 5: Commit**

```bash
git add datasci/ttest.py tests/test_ttest.py
git commit -m "feat(datasci): add two-sample t-test"
```

---

## Task 1.6: `datasci/fisher.py` — `fishers_exact_test`

**Files:**
- Create: `datasci/fisher.py`
- Create: `tests/test_fisher.py`

**Source:** `../ctsi-mao/utils/stats_utils.py` lines 126–132.

- [ ] **Step 1: Write failing test**

Write to `tests/test_fisher.py`:

```python
import pandas as pd
import numpy as np

def test_fisher_exact_2x2_obvious():
    from datasci.fisher import fishers_exact_test
    df = pd.DataFrame({
        "group": ["A"] * 10 + ["B"] * 10,
        "outcome": [1] * 9 + [0] * 1 + [0] * 9 + [1] * 1,
    })
    r = fishers_exact_test(df, "group", "outcome")
    assert r["p_value"] < 0.01
    assert not np.isnan(r["odds_ratio"])

def test_fisher_exact_non_2x2():
    from datasci.fisher import fishers_exact_test
    df = pd.DataFrame({
        "x": ["a", "b", "c", "a", "b", "c"],
        "y": [1, 0, 1, 0, 1, 0],
    })
    r = fishers_exact_test(df, "x", "y")
    assert np.isnan(r["p_value"])
    assert "note" in r
```

- [ ] **Step 2: Run to verify failure**

Run: `tests/run.sh tests/test_fisher.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement**

Write to `datasci/fisher.py`:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "numpy>=1.20",
#   "pandas>=1.3",
#   "scipy>=1.7",
# ]
# ///
"""Fisher's exact test for 2x2 contingency tables."""

from typing import Dict
import numpy as np
import pandas as pd
from scipy import stats as scipy_stats


def fishers_exact_test(df: pd.DataFrame, var1: str, var2: str) -> Dict:
    """Fisher's exact test for 2x2 tables."""
    contingency = pd.crosstab(df[var1].dropna(), df[var2].dropna())
    if contingency.shape == (2, 2):
        odds_ratio, p_value = scipy_stats.fisher_exact(contingency)
        return {"odds_ratio": odds_ratio, "p_value": p_value, "contingency": contingency}
    return {"odds_ratio": np.nan, "p_value": np.nan, "note": "Not a 2x2 table"}
```

- [ ] **Step 4: Run to verify pass**

Run: `tests/run.sh tests/test_fisher.py -v`
Expected: both tests pass.

- [ ] **Step 5: Commit**

```bash
git add datasci/fisher.py tests/test_fisher.py
git commit -m "feat(datasci): add Fisher's exact test"
```

---

## Task 1.7: `datasci/chisquare.py` — `perform_chi_square`

**Files:**
- Create: `datasci/chisquare.py`
- Create: `tests/test_chisquare.py`

**Source:** `../ctsi-mao/utils/stats_utils.py` lines 33–78. The function picks its method (chi-square / Fisher's / Monte Carlo Fisher-Freeman-Halton) based on table shape and sparsity — preserve that logic verbatim.

- [ ] **Step 1: Write failing test**

Write to `tests/test_chisquare.py`:

```python
import pandas as pd
import numpy as np

def test_chi_square_2x2_normal():
    from datasci.chisquare import perform_chi_square
    df = pd.DataFrame({
        "group": ["A"] * 50 + ["B"] * 50,
        "outcome": [1] * 40 + [0] * 10 + [0] * 40 + [1] * 10,
    })
    r = perform_chi_square(df, "group", "outcome")
    assert r["p_value"] < 0.001
    assert "chi-square" in r["method"]
    assert r["n"] == 100

def test_chi_square_2x2_with_zero_cell_falls_back_to_fisher():
    from datasci.chisquare import perform_chi_square
    df = pd.DataFrame({
        "group": ["A"] * 5 + ["B"] * 5,
        "outcome": [1] * 5 + [0] * 5,
    })
    r = perform_chi_square(df, "group", "outcome")
    assert r["method"] == "Fisher's exact"

def test_chi_square_rxc_table():
    from datasci.chisquare import perform_chi_square
    np.random.seed(0)
    df = pd.DataFrame({
        "x": np.random.choice(["a", "b", "c"], 200),
        "y": np.random.choice([1, 2, 3], 200),
    })
    r = perform_chi_square(df, "x", "y")
    assert "chi2_statistic" in r
    assert 0.0 <= r["p_value"] <= 1.0
```

- [ ] **Step 2: Run to verify failure**

Run: `tests/run.sh tests/test_chisquare.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement**

Write to `datasci/chisquare.py`:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "numpy>=1.20",
#   "pandas>=1.3",
#   "scipy>=1.7",
# ]
# ///
"""Chi-square test of independence (with appropriate fallbacks)."""

from typing import Dict
import numpy as np
import pandas as pd
from scipy import stats as scipy_stats


def perform_chi_square(data: pd.DataFrame, col1: str, col2: str) -> Dict:
    """Test of association for categorical variables.

    2x2 tables: chi-square with Yates' correction (Fisher's exact if any cell is 0).
    r×c tables with expected < 5: Monte Carlo Fisher-Freeman-Halton simulation.
    Otherwise: chi-square test of independence.
    """
    contingency = pd.crosstab(data[col1], data[col2])
    n = contingency.sum().sum()
    ct = contingency.values
    chi2, _, dof, expected = scipy_stats.chi2_contingency(ct)

    if contingency.shape == (2, 2):
        if (ct == 0).any():
            _, p_val = scipy_stats.fisher_exact(ct)
            method = "Fisher's exact"
        else:
            chi2, p_val, dof, expected = scipy_stats.chi2_contingency(ct, correction=True)
            method = "chi-square (Yates')"
    elif (expected < 5).any():
        row_sums = ct.sum(axis=1)
        col_sums = ct.sum(axis=0)
        probs = np.outer(row_sums, col_sums).ravel() / n**2
        rng = np.random.default_rng(42)
        n_sim = 9999
        count = 0
        for _ in range(n_sim):
            sim = rng.multinomial(n, probs).reshape(ct.shape)
            try:
                if scipy_stats.chi2_contingency(sim)[0] >= chi2:
                    count += 1
            except ValueError:
                pass
        p_val = (count + 1) / (n_sim + 1)
        method = "Monte Carlo Fisher-Freeman-Halton"
    else:
        _, p_val, _, _ = scipy_stats.chi2_contingency(ct)
        method = "chi-square"

    min_dim = min(contingency.shape) - 1
    cramers_v = np.sqrt(chi2 / (n * min_dim)) if min_dim > 0 else 0
    return {
        "chi2_statistic": chi2, "p_value": p_val,
        "dof": dof, "cramers_v": cramers_v, "n": n,
        "contingency_table": contingency, "method": method,
    }
```

- [ ] **Step 4: Run to verify pass**

Run: `tests/run.sh tests/test_chisquare.py -v`
Expected: all 3 tests pass. (Monte Carlo case will take a few seconds.)

- [ ] **Step 5: Commit**

```bash
git add datasci/chisquare.py tests/test_chisquare.py
git commit -m "feat(datasci): add chi-square test with method auto-selection"
```

---

## Task 1.8: `datasci/report.py` — markdown report builders

**Files:**
- Create: `datasci/report.py`
- Create: `tests/test_report.py`

**Source:** `../ctsi-mao/utils/reporting.py` (whole file, all 5 functions). One change: replace `from utils.stats_utils import format_p_value` with `from datasci.pvalues import format_p_value` (intra-`datasci/` import — Task 1.2 must be complete).

- [ ] **Step 1: Write failing test**

Write to `tests/test_report.py`:

```python
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
```

- [ ] **Step 2: Run to verify failure**

Run: `tests/run.sh tests/test_report.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement**

Write to `datasci/report.py`:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pandas>=1.3",
#   "tabulate>=0.9",
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
```

**Genericization note vs. ctsi-mao source:**
- `save_markdown_report` and `generate_report` used `Path(__file__).parent.parent / output_dir` (assumed installed in a sibling `utils/` dir of the project). Changed to `Path.cwd() / output_dir` so the function lands files relative to the consumer's working directory regardless of where `datasci/` itself lives.
- The `format_p_value` import is changed from `from utils.stats_utils` to `from datasci.pvalues` (intra-`datasci/` sibling import).

- [ ] **Step 4: Run to verify pass**

Run: `tests/run.sh tests/test_report.py -v`
Expected: all 5 tests pass.

- [ ] **Step 5: Commit**

```bash
git add datasci/report.py tests/test_report.py
git commit -m "feat(datasci): add markdown report builders"
```

---

## Task 1.9: `datasci/diverging_bar.py` — move from `viztools/charts.py`

**Files:**
- Create: `datasci/diverging_bar.py`
- Create: `tests/test_diverging_bar.py`
- Delete (later, in Task 5.3): `viztools/`

**Source:** current repo's `viztools/charts.py` — move as-is, prepend PEP 723 header.

- [ ] **Step 1: Write failing test**

Write to `tests/test_diverging_bar.py`:

```python
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
```

- [ ] **Step 2: Run to verify failure**

Run: `tests/run.sh tests/test_diverging_bar.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement**

Move the existing file with git so history is preserved:

```bash
git mv viztools/charts.py datasci/diverging_bar.py
```

Then prepend the PEP 723 header to the file. Open `datasci/diverging_bar.py` and insert these lines at the top (before the existing `import numpy as np`):

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "numpy>=1.20",
#   "pandas>=1.3",
#   "matplotlib>=3.4",
# ]
# ///
"""Diverging bar chart for Likert/ordinal data with auto-split neutral category."""

```

Leave the rest of the file unchanged.

- [ ] **Step 4: Run to verify pass**

Run: `tests/run.sh tests/test_diverging_bar.py -v`
Expected: both tests pass.

- [ ] **Step 5: Commit**

```bash
git add datasci/diverging_bar.py tests/test_diverging_bar.py
git commit -m "feat(datasci): move diverging_bar from viztools, add PEP 723 header"
```

(The `viztools/` directory will be deleted in Task 5.3; for now leave the empty dir + `__init__.py` alone so this commit is focused on the move.)

---

## Task 1.10: `datasci/histogram.py` — genericized `create_histogram`

**Files:**
- Create: `datasci/histogram.py`
- Create: `tests/test_histogram.py`

**Source:** `../ctsi-mao/utils/viz_utils.py` lines 163–192 + the helper `_count_at_cutpoint` (lines 51–56).

**Genericization:** replace `figsize = figsize or _get_figsize()` (reads `PLOT_SETTINGS`) with `figsize = figsize or (8, 6)`. Replace `_save_fig(fig, save_path)` (reads `PLOT_SETTINGS['dpi']`) with inline `fig.savefig(save_path, dpi=dpi, bbox_inches='tight'); plt.close(fig)`. Add `dpi: int = 300` kwarg.

- [ ] **Step 1: Write failing test**

Write to `tests/test_histogram.py`:

```python
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
```

- [ ] **Step 2: Run to verify failure**

Run: `tests/run.sh tests/test_histogram.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement**

Write to `datasci/histogram.py`:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "numpy>=1.20",
#   "pandas>=1.3",
#   "matplotlib>=3.4",
# ]
# ///
"""Histogram with optional cutpoint annotation."""

from typing import Optional, Tuple
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd


def _count_at_cutpoint(data: pd.Series, cutpoint: float, operator: str) -> int:
    ops = {'<=': data <= cutpoint, '<': data < cutpoint,
           '>=': data >= cutpoint, '>': data > cutpoint}
    if operator not in ops:
        raise ValueError(f"Unknown operator '{operator}'; must be one of: <=, <, >=, >")
    return int(ops[operator].sum())


def create_histogram(data: pd.Series, title: str, xlabel: str,
                     bins: Optional[int] = None,
                     figsize: Optional[Tuple[float, float]] = None,
                     save_path: Optional[str] = None,
                     cutpoint: Optional[float] = None,
                     cutpoint_label: Optional[str] = None,
                     cutpoint_operator: Optional[str] = None,
                     dpi: int = 300) -> plt.Figure:
    """Create a standardized histogram with optional cutpoint annotation."""
    figsize = figsize or (8, 6)
    bins = bins or 20
    clean = data.dropna()
    fig, ax = plt.subplots(figsize=figsize)
    ax.hist(clean, bins=bins, alpha=0.7, color='skyblue', edgecolor='black')
    ax.set_xlabel(xlabel)
    ax.set_ylabel('Frequency')
    ax.set_title(title)
    ax.grid(True, alpha=0.3)

    if cutpoint is not None:
        op = cutpoint_operator or '<='
        ax.axvline(x=cutpoint, color='red', linestyle='--', linewidth=2, alpha=0.8)
        n_at_cut = _count_at_cutpoint(clean, cutpoint, op)
        label_text = cutpoint_label or f"Cutpoint: {cutpoint}"
        ax.text(cutpoint, ax.get_ylim()[1] * 0.95,
                f"  {label_text}\n  n={n_at_cut} ({n_at_cut/len(clean)*100:.1f}%)",
                color='red', fontsize=9, va='top')

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=dpi, bbox_inches='tight')
        plt.close(fig)
    return fig
```

- [ ] **Step 4: Run to verify pass**

Run: `tests/run.sh tests/test_histogram.py -v`
Expected: both tests pass.

- [ ] **Step 5: Commit**

```bash
git add datasci/histogram.py tests/test_histogram.py
git commit -m "feat(datasci): add histogram (genericized from ctsi-mao)"
```

---

## Task 1.11: `datasci/bar.py` — genericized `create_bar_plot`

**Files:**
- Create: `datasci/bar.py`
- Create: `tests/test_bar.py`

**Source:** `../ctsi-mao/utils/viz_utils.py` lines 195–212.

**Genericization:** same as Task 1.10 — replace `_get_figsize()` with `(8, 6)` default; inline the savefig logic with `dpi` kwarg.

- [ ] **Step 1: Write failing test**

Write to `tests/test_bar.py`:

```python
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
```

- [ ] **Step 2: Run to verify failure**

Run: `tests/run.sh tests/test_bar.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement**

Write to `datasci/bar.py`:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "numpy>=1.20",
#   "matplotlib>=3.4",
# ]
# ///
"""Standardized bar plot."""

from typing import List, Optional, Tuple
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def create_bar_plot(categories: List[str], values: List[float],
                    title: str, xlabel: str, ylabel: str,
                    figsize: Optional[Tuple[float, float]] = None,
                    save_path: Optional[str] = None,
                    dpi: int = 300) -> plt.Figure:
    """Create a standardized bar plot."""
    figsize = figsize or (8, 6)
    fig, ax = plt.subplots(figsize=figsize)
    x = np.arange(len(categories))
    ax.bar(x, values, alpha=0.7)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels(categories, rotation=45, ha='right')
    ax.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=dpi, bbox_inches='tight')
        plt.close(fig)
    return fig
```

- [ ] **Step 4: Run to verify pass**

Run: `tests/run.sh tests/test_bar.py -v`
Expected: test passes.

- [ ] **Step 5: Commit**

```bash
git add datasci/bar.py tests/test_bar.py
git commit -m "feat(datasci): add bar plot (genericized from ctsi-mao)"
```

---

## Task 1.12: `datasci/logrank.py` — `perform_logrank`

**Files:**
- Create: `datasci/logrank.py`
- Create: `tests/test_logrank.py`

**Source:** `../ctsi-mao/utils/stats_utils.py` lines 223–254. Keep the `from lifelines.statistics import ...` import **inside** the function body (lazy — already is in source).

- [ ] **Step 1: Write failing test**

Write to `tests/test_logrank.py`:

```python
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
```

- [ ] **Step 2: Run to verify failure**

Run: `tests/run.sh tests/test_logrank.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement**

Write to `datasci/logrank.py`:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "numpy>=1.20",
#   "pandas>=1.3",
#   "lifelines>=0.27",
# ]
# ///
"""Log-rank test for survival group comparison."""

from typing import Dict
import numpy as np
import pandas as pd


def perform_logrank(durations: pd.Series, event_observed: pd.Series,
                    group: pd.Series) -> Dict:
    """Log-rank test comparing groups."""
    from lifelines.statistics import logrank_test, multivariate_logrank_test

    mask = durations.notna() & event_observed.notna() & group.notna()
    dur = durations[mask]
    evt = event_observed[mask]
    grp = group[mask]

    unique_groups = sorted(grp.unique())
    if len(unique_groups) < 2:
        return {"test_statistic": np.nan, "p_value": np.nan,
                "note": f"Expected ≥2 groups, got {len(unique_groups)}"}

    if len(unique_groups) == 2:
        g1_mask = grp == unique_groups[0]
        result = logrank_test(
            dur[g1_mask], dur[~g1_mask],
            evt[g1_mask], evt[~g1_mask],
        )
    else:
        result = multivariate_logrank_test(dur, grp, evt)

    n_per_group = {str(g): int((grp == g).sum()) for g in unique_groups}
    return {
        "test_statistic": result.test_statistic,
        "p_value": result.p_value,
        "groups": list(unique_groups),
        "n_per_group": n_per_group,
    }
```

- [ ] **Step 4: Run to verify pass**

Run: `tests/run.sh tests/test_logrank.py -v`
Expected: both tests pass.

- [ ] **Step 5: Commit**

```bash
git add datasci/logrank.py tests/test_logrank.py
git commit -m "feat(datasci): add log-rank test"
```

---

## Task 1.13: `datasci/km.py` — Kaplan-Meier (fit + plot)

**Files:**
- Create: `datasci/km.py`
- Create: `tests/test_km.py`

**Source:**
- `fit_km`, `fit_km_by_group`, `km_at_timepoints` from `../ctsi-mao/utils/stats_utils.py` lines 137–220.
- `plot_km`, `plot_loglog` from `../ctsi-mao/utils/viz_utils.py` lines 217–358.

**Genericization (plotting):** drop `PLOT_SETTINGS`-based `_get_figsize()`, `_save_fig()`, `_build_color_map()` helpers. Replace with:
- `figsize` kwarg, default `(8, 6)`.
- `dpi` kwarg, default 300.
- `color_map: Optional[Dict[str, str]] = None` kwarg — if None, use matplotlib default `Set1` cycle.
- Inline savefig: `if save_path: fig.savefig(save_path, dpi=dpi, bbox_inches='tight'); plt.close(fig)`.

Replace `from utils.stats_utils import format_p_value` (used in `plot_km`) with `from datasci.pvalues import format_p_value`.

- [ ] **Step 1: Write failing test**

Write to `tests/test_km.py`:

```python
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
```

- [ ] **Step 2: Run to verify failure**

Run: `tests/run.sh tests/test_km.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement**

Write to `datasci/km.py`:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "numpy>=1.20",
#   "pandas>=1.3",
#   "matplotlib>=3.4",
#   "lifelines>=0.27",
# ]
# ///
"""Kaplan-Meier survival analysis: fitting + plotting + at-risk tables."""

from typing import Dict, List, Optional, Tuple
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd


def fit_km(durations: pd.Series, event_observed: pd.Series, label: str = None):
    """Fit a Kaplan-Meier estimator. Returns the fitted KaplanMeierFitter."""
    from lifelines import KaplanMeierFitter
    kmf = KaplanMeierFitter()
    mask = durations.notna() & event_observed.notna()
    kmf.fit(durations[mask], event_observed[mask], label=label)
    return kmf


def fit_km_by_group(df: pd.DataFrame, group_col: str, time_col: str,
                    event_col: str, group_labels: Dict = None,
                    min_n: int = 1) -> Dict:
    """Fit KM curves for each group in a column.

    Args:
        group_labels: Dict mapping raw values → display labels.
            If None, uses unique values as-is.
        min_n: Minimum group size to include.

    Returns dict mapping label → fitted KaplanMeierFitter.
    """
    if group_labels is None:
        group_labels = {g: str(g) for g in sorted(df[group_col].dropna().unique())}
    kmf_dict = {}
    for code, label in group_labels.items():
        mask = df[group_col] == code
        if mask.sum() >= min_n:
            kmf_dict[label] = fit_km(df.loc[mask, time_col],
                                     df.loc[mask, event_col], label=label)
    return kmf_dict


def km_at_timepoints(kmf, timepoints: List[int]) -> pd.DataFrame:
    """Extract KM estimates at specific timepoints.

    Returns DataFrame with columns: timepoint, survival, cumulative_incidence,
    ci_lower, ci_upper, n_at_risk, formatted.
    """
    rows = []
    for t in timepoints:
        s_t = float(kmf.predict(t))
        ci_1 = 1 - s_t

        ci_df = kmf.confidence_interval_survival_function_
        valid_idx = ci_df.index[ci_df.index <= t]
        if len(valid_idx) > 0:
            idx = valid_idx[-1]
            s_lower = float(ci_df.iloc[:, 0].loc[idx])
            s_upper = float(ci_df.iloc[:, 1].loc[idx])
            ci_ci_lower = 1 - s_upper
            ci_ci_upper = 1 - s_lower
        else:
            ci_ci_lower = 0.0
            ci_ci_upper = 0.0

        et = kmf.event_table
        at_risk_rows = et.index[et.index <= t]
        if len(at_risk_rows) > 0:
            last_t = at_risk_rows[-1]
            n_at_risk = int(et.loc[last_t, 'at_risk'] - et.loc[last_t, 'observed'] - et.loc[last_t, 'censored'])
        else:
            n_at_risk = int(et.iloc[0]['at_risk']) if len(et) > 0 else 0

        formatted = f"{ci_1 * 100:.1f}% ({ci_ci_lower * 100:.1f}–{ci_ci_upper * 100:.1f}%)"
        rows.append({
            "timepoint": t,
            "survival": s_t,
            "cumulative_incidence": ci_1,
            "ci_lower": ci_ci_lower,
            "ci_upper": ci_ci_upper,
            "n_at_risk": n_at_risk,
            "formatted": formatted,
        })
    return pd.DataFrame(rows)


def _resolve_colors(group_labels: List[str],
                    color_map: Optional[Dict[str, str]]) -> Dict[str, str]:
    """Build a color lookup from optional override + matplotlib Set1 fallback."""
    color_map = color_map or {}
    default_colors = plt.cm.Set1(np.linspace(0, 1, max(len(group_labels), 2)))
    resolved = {}
    for i, label in enumerate(group_labels):
        resolved[label] = color_map.get(label, default_colors[i])
    return resolved


def plot_km(kmf_dict: Dict, title: str,
            timepoints: List[int],
            p_value: Optional[float] = None,
            save_path: Optional[str] = None,
            show_ci: bool = True,
            xlabel: str = "Time",
            ylabel: str = "Survival Probability",
            invert: bool = False,
            xlim: Optional[Tuple[float, float]] = None,
            figsize: Tuple[float, float] = (8, 6),
            dpi: int = 300,
            color_map: Optional[Dict[str, str]] = None) -> plt.Figure:
    """Plot KM survival curves with a number-at-risk table.

    Args:
        kmf_dict: Dict mapping group label -> fitted KaplanMeierFitter
        title: Plot title
        timepoints: Landmark timepoints for at-risk table (required)
        p_value: Log-rank p-value to annotate
        save_path: Path to save figure
        show_ci: Show confidence intervals
        xlabel, ylabel: Axis labels
        invert: If True, plot 1-S(t) (cumulative incidence) instead of S(t)
        xlim: Optional (xmin, xmax). When set, at-risk table also filters to timepoints <= xmax.
        figsize, dpi: Matplotlib sizing
        color_map: Optional {label: color} override; falls back to Set1
    """
    from datasci.pvalues import format_p_value

    if xlim is not None:
        timepoints = [t for t in timepoints if t <= xlim[1]]
    group_labels = list(kmf_dict.keys())
    colors = _resolve_colors(group_labels, color_map)

    fig = plt.figure(figsize=figsize)
    gs = gridspec.GridSpec(2, 1, height_ratios=[4, 1], hspace=0.05)
    ax_main = fig.add_subplot(gs[0])
    ax_risk = fig.add_subplot(gs[1], sharex=ax_main)

    for label, kmf in kmf_dict.items():
        color = colors[label]
        times = kmf.survival_function_.index
        surv = kmf.survival_function_.values.flatten()
        y_vals = (1 - surv) if invert else surv

        ax_main.step(times, y_vals, where='post', color=color, linewidth=2, label=label)

        if show_ci:
            ci = kmf.confidence_interval_survival_function_
            ci_low = ci.iloc[:, 0].values
            ci_high = ci.iloc[:, 1].values
            if invert:
                ci_low, ci_high = 1 - ci_high, 1 - ci_low
            ax_main.fill_between(times, ci_low, ci_high, step='post',
                                 alpha=0.15, color=color)

    if p_value is not None:
        p_text = f"Log-rank p = {format_p_value(p_value)}"
        ax_main.text(0.98, 0.95, p_text, transform=ax_main.transAxes,
                     ha='right', va='top', fontsize=11,
                     bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    for t in timepoints:
        if t > 0:
            ax_main.axvline(x=t, color='gray', linestyle=':', alpha=0.3)

    ax_main.set_ylabel(ylabel)
    ax_main.set_xlabel(xlabel)
    ax_main.set_title(title)
    ax_main.set_ylim(bottom=0, top=1.05)
    if xlim is not None:
        ax_main.set_xlim(xlim)
    else:
        ax_main.set_xlim(left=0)
    ax_main.grid(True, alpha=0.3)
    ax_main.legend(loc='best')
    plt.setp(ax_main.get_xticklabels(), visible=False)

    ax_risk.axis('off')
    row_labels = list(kmf_dict.keys())
    cell_text = []
    for label, kmf in kmf_dict.items():
        et = kmf.event_table
        n_at_risk_row = []
        for t in timepoints:
            valid = et.index[et.index <= t]
            if len(valid) > 0:
                last_t = valid[-1]
                nar = int(et.loc[last_t, 'at_risk'] - et.loc[last_t, 'observed'] - et.loc[last_t, 'censored'])
                if t == 0:
                    nar = int(et.iloc[0]['at_risk'])
                n_at_risk_row.append(str(max(nar, 0)))
            else:
                n_at_risk_row.append(str(int(et.iloc[0]['at_risk'])))
        cell_text.append(n_at_risk_row)

    col_labels = [str(t) for t in timepoints]
    table = ax_risk.table(cellText=cell_text, rowLabels=row_labels,
                          colLabels=col_labels, loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.2)

    fig.subplots_adjust(left=0.1, right=0.95, top=0.92, bottom=0.08, hspace=0.05)
    if save_path:
        fig.savefig(save_path, dpi=dpi, bbox_inches='tight')
        plt.close(fig)
    return fig


def plot_loglog(kmf_dict: Dict, save_path: Optional[str] = None,
                title: str = "Log-Log Survival Plot (PH Check)",
                figsize: Tuple[float, float] = (8, 6),
                dpi: int = 300,
                color_map: Optional[Dict[str, str]] = None) -> plt.Figure:
    """Plot log(-log(S(t))) vs log(t) for proportional hazards visual check.

    Parallel lines suggest PH assumption holds.
    """
    group_labels = list(kmf_dict.keys())
    colors = _resolve_colors(group_labels, color_map)

    fig, ax = plt.subplots(figsize=figsize)

    for label, kmf in kmf_dict.items():
        color = colors[label]
        sf = kmf.survival_function_.copy()
        sf = sf[sf.iloc[:, 0] > 0]
        sf = sf[sf.index > 0]
        log_t = np.log(sf.index)
        log_neg_log_s = np.log(-np.log(sf.values.flatten()))
        ax.plot(log_t, log_neg_log_s, label=label, color=color, linewidth=2)

    ax.set_xlabel('log(time)')
    ax.set_ylabel('log(-log(S(t)))')
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    ax.legend()
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=dpi, bbox_inches='tight')
        plt.close(fig)
    return fig
```

- [ ] **Step 4: Run to verify pass**

Run: `tests/run.sh tests/test_km.py -v`
Expected: all 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add datasci/km.py tests/test_km.py
git commit -m "feat(datasci): add Kaplan-Meier (fit + plot, genericized)"
```

---

## Task 1.14: `datasci/cox.py` — Cox PH regression

**Files:**
- Create: `datasci/cox.py`
- Create: `tests/test_cox.py`

**Source:** `../ctsi-mao/utils/stats_utils.py` lines 259–406 — `_prepare_cox_data`, `fit_cox_univariate`, `fit_cox_multivariable`, `cox_summary_table`, `check_proportional_hazards`.

**Genericization:** `cox_summary_table` imports `format_p_value` from `utils.stats_utils` → change to `from datasci.pvalues import format_p_value`. All `lifelines` imports already lazy inside function bodies — keep that.

- [ ] **Step 1: Write failing test**

Write to `tests/test_cox.py`:

```python
import numpy as np
import pandas as pd

def _toy_survival_df(n=200, seed=0):
    rng = np.random.RandomState(seed)
    age = rng.normal(60, 10, n)
    sex = rng.choice([0, 1], n)
    time = rng.exponential(scale=10, size=n)
    event = rng.choice([0, 1], n, p=[0.3, 0.7])
    return pd.DataFrame({"time": time, "event": event, "age": age, "sex": sex})

def test_fit_cox_univariate_continuous():
    from datasci.cox import fit_cox_univariate
    df = _toy_survival_df()
    out = fit_cox_univariate(df, "time", "event", "age")
    assert len(out) == 1
    assert "hr" in out[0]
    assert out[0]["n"] == len(df)

def test_fit_cox_multivariable_returns_fitter_and_data():
    from datasci.cox import fit_cox_multivariable
    df = _toy_survival_df()
    cph, model_df = fit_cox_multivariable(df, "time", "event", ["age", "sex"])
    assert hasattr(cph, "summary")
    assert len(model_df) == len(df)

def test_cox_summary_table_uses_pvalues_format():
    from datasci.cox import fit_cox_multivariable, cox_summary_table
    df = _toy_survival_df()
    cph, _ = fit_cox_multivariable(df, "time", "event", ["age"])
    t = cox_summary_table(cph)
    assert "Variable" in t.columns
    assert "HR" in t.columns
    assert "p-value" in t.columns

def test_check_proportional_hazards_returns_dict():
    from datasci.cox import fit_cox_multivariable, check_proportional_hazards
    df = _toy_survival_df()
    cph, model_df = fit_cox_multivariable(df, "time", "event", ["age", "sex"])
    r = check_proportional_hazards(cph, model_df)
    assert "test_name" in r
```

- [ ] **Step 2: Run to verify failure**

Run: `tests/run.sh tests/test_cox.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement**

Write to `datasci/cox.py`:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "numpy>=1.20",
#   "pandas>=1.3",
#   "lifelines>=0.27",
# ]
# ///
"""Cox proportional hazards regression: fitting, summary, PH check."""

from typing import Dict, List, Optional
import numpy as np
import pandas as pd


def _prepare_cox_data(df: pd.DataFrame, time_col: str, event_col: str,
                      covariates: List[str], categorical_vars: List[str] = None,
                      reference_categories: Dict = None) -> pd.DataFrame:
    """Prepare DataFrame for Cox regression: select cols, encode categoricals, drop NaN."""
    categorical_vars = categorical_vars or []
    reference_categories = reference_categories or {}

    cols = [time_col, event_col] + covariates
    model_df = df[cols].copy()

    for cat_var in categorical_vars:
        if cat_var in model_df.columns:
            ref = reference_categories.get(cat_var)
            dummies = pd.get_dummies(model_df[cat_var], prefix=cat_var, drop_first=False)
            if ref:
                ref_col = f"{cat_var}_{ref}"
                if ref_col in dummies.columns:
                    dummies = dummies.drop(columns=[ref_col])
            else:
                dummies = dummies.iloc[:, 1:]
            model_df = model_df.drop(columns=[cat_var])
            model_df = pd.concat([model_df, dummies], axis=1)

    for col in model_df.columns:
        if col not in [time_col, event_col]:
            model_df[col] = pd.to_numeric(model_df[col], errors='coerce')

    model_df = model_df.dropna()
    return model_df


def fit_cox_univariate(df: pd.DataFrame, time_col: str, event_col: str,
                       covariate: str, display_name: str = None,
                       categorical_vars: List[str] = None,
                       reference_categories: Dict = None) -> List[Dict]:
    """Univariate Cox regression for a single covariate.

    Returns list of dicts (one per level for categoricals, one for continuous/binary).
    Each dict has: variable, hr, ci_lower, ci_upper, p_value, n, events.
    """
    from lifelines import CoxPHFitter

    categorical_vars = categorical_vars or []
    reference_categories = reference_categories or {}
    is_categorical = covariate in categorical_vars

    model_df = _prepare_cox_data(df, time_col, event_col, [covariate],
                                 categorical_vars=[covariate] if is_categorical else [],
                                 reference_categories=reference_categories)

    if len(model_df) < 10:
        return [{"variable": display_name or covariate,
                 "hr": np.nan, "ci_lower": np.nan, "ci_upper": np.nan,
                 "p_value": np.nan, "n": len(model_df),
                 "events": int(model_df[event_col].sum()),
                 "note": "Insufficient observations"}]

    try:
        cph = CoxPHFitter()
        cph.fit(model_df, duration_col=time_col, event_col=event_col)
        summary = cph.summary

        results = []
        for idx in summary.index:
            var_label = display_name or covariate
            if is_categorical:
                level = idx.replace(f"{covariate}_", "")
                ref = reference_categories.get(covariate, "ref")
                var_label = f"{display_name or covariate}: {level} vs {ref}"
            results.append({
                "variable": var_label,
                "hr": float(summary.loc[idx, 'exp(coef)']),
                "ci_lower": float(summary.loc[idx, 'exp(coef) lower 95%']),
                "ci_upper": float(summary.loc[idx, 'exp(coef) upper 95%']),
                "p_value": float(summary.loc[idx, 'p']),
                "n": len(model_df),
                "events": int(model_df[event_col].sum()),
            })
        return results
    except Exception as e:
        return [{"variable": display_name or covariate,
                 "hr": np.nan, "ci_lower": np.nan, "ci_upper": np.nan,
                 "p_value": np.nan, "n": len(model_df),
                 "events": int(model_df[event_col].sum()),
                 "note": f"Model failed: {str(e)}"}]


def fit_cox_multivariable(df: pd.DataFrame, time_col: str, event_col: str,
                          covariates: List[str], categorical_vars: List[str] = None,
                          reference_categories: Dict = None):
    """Fit multivariable Cox PH model. Returns (fitted CoxPHFitter, model_df)."""
    from lifelines import CoxPHFitter
    model_df = _prepare_cox_data(df, time_col, event_col, covariates,
                                 categorical_vars=categorical_vars,
                                 reference_categories=reference_categories)
    cph = CoxPHFitter()
    cph.fit(model_df, duration_col=time_col, event_col=event_col)
    return cph, model_df


def cox_summary_table(cph, rename: Dict = None) -> pd.DataFrame:
    """Extract Cox model summary as a clean DataFrame for reporting."""
    from datasci.pvalues import format_p_value
    rename = rename or {}
    s = cph.summary.copy()
    rows = []
    for idx in s.index:
        rows.append({
            "Variable": rename.get(idx, idx),
            "HR": f"{s.loc[idx, 'exp(coef)']:.2f}",
            "95% CI": f"({s.loc[idx, 'exp(coef) lower 95%']:.2f}–{s.loc[idx, 'exp(coef) upper 95%']:.2f})",
            "p-value": format_p_value(s.loc[idx, 'p']),
        })
    return pd.DataFrame(rows)


def check_proportional_hazards(cph, training_df=None) -> Dict:
    """Check PH assumption via Schoenfeld residuals test.

    Args:
        cph: Fitted CoxPHFitter
        training_df: The DataFrame used to fit (required by lifelines)
    """
    try:
        from lifelines.statistics import proportional_hazard_test
        test_results = proportional_hazard_test(cph, training_df, time_transform='rank')
        return {"summary": test_results.summary, "test_name": "Schoenfeld residuals test"}
    except Exception as e:
        return {"error": str(e), "test_name": "Schoenfeld residuals test"}
```

- [ ] **Step 4: Run to verify pass**

Run: `tests/run.sh tests/test_cox.py -v`
Expected: all 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add datasci/cox.py tests/test_cox.py
git commit -m "feat(datasci): add Cox PH regression"
```

---

## Task 1.15: `datasci/forest.py` — `plot_forest`

**Files:**
- Create: `datasci/forest.py`
- Create: `tests/test_forest.py`

**Source:** `../ctsi-mao/utils/viz_utils.py` lines 361–424.

**Genericization:** replace `PLOT_SETTINGS['forest_color']` with `forest_color: str = '#1f77b4'` kwarg. Replace `_save_fig` with inline savefig + `dpi` kwarg.

- [ ] **Step 1: Write failing test**

Write to `tests/test_forest.py`:

```python
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
```

- [ ] **Step 2: Run to verify failure**

Run: `tests/run.sh tests/test_forest.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement**

Write to `datasci/forest.py`:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "numpy>=1.20",
#   "pandas>=1.3",
#   "matplotlib>=3.4",
# ]
# ///
"""Forest plot for regression results."""

from typing import Optional
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def plot_forest(results_df: pd.DataFrame,
                save_path: Optional[str] = None,
                title: str = "Forest Plot — Hazard Ratios",
                effect_col: str = 'hr',
                effect_label: str = 'Hazard Ratio (95% CI)',
                forest_color: str = '#1f77b4',
                dpi: int = 300) -> plt.Figure:
    """Create a forest plot from regression results.

    Args:
        results_df: DataFrame with columns: variable, [effect_col], ci_lower, ci_upper, p_value
        save_path: Path to save figure
        title: Plot title
        effect_col: Column name for the effect estimate (default 'hr')
        effect_label: X-axis label
        forest_color: Marker/CI color
        dpi: Save DPI
    """
    df = results_df.dropna(subset=[effect_col]).copy()
    if len(df) == 0:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, 'No valid results for forest plot',
                ha='center', va='center', transform=ax.transAxes)
        if save_path:
            fig.savefig(save_path, dpi=dpi, bbox_inches='tight')
            plt.close(fig)
        return fig

    df = df.iloc[::-1]
    y_pos = np.arange(len(df))

    fig, ax = plt.subplots(figsize=(10, max(4, len(df) * 0.5 + 1)))

    has_ci = df['ci_lower'].notna() & df['ci_upper'].notna()
    df_ci = df[has_ci]
    df_no_ci = df[~has_ci]

    if len(df_ci) > 0:
        ci_positions = [list(df.index).index(i) for i in df_ci.index]
        ax.errorbar(df_ci[effect_col].values, ci_positions,
                    xerr=[df_ci[effect_col].values - df_ci['ci_lower'].values,
                          df_ci['ci_upper'].values - df_ci[effect_col].values],
                    fmt='o', color=forest_color, markersize=6, capsize=3, linewidth=1.5)

    if len(df_no_ci) > 0:
        no_ci_positions = [list(df.index).index(i) for i in df_no_ci.index]
        ax.plot(df_no_ci[effect_col].values, no_ci_positions,
                'D', color='#ff7f0e', markersize=6)

    ax.axvline(x=1.0, color='red', linestyle='--', alpha=0.7, linewidth=1)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(df['variable'])
    ax.set_xlabel(effect_label)
    ax.set_title(title)
    ax.grid(True, alpha=0.3, axis='x')

    for i, (idx, row) in enumerate(df.iterrows()):
        if pd.notna(row['ci_lower']) and pd.notna(row['ci_upper']):
            text = f"{row[effect_col]:.2f} ({row['ci_lower']:.2f}–{row['ci_upper']:.2f})"
        else:
            text = f"{row[effect_col]:.2f} (no CI)"
        ax.text(ax.get_xlim()[1] * 1.02, y_pos[i], text, va='center', fontsize=8)

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=dpi, bbox_inches='tight')
        plt.close(fig)
    return fig
```

- [ ] **Step 4: Run to verify pass**

Run: `tests/run.sh tests/test_forest.py -v`
Expected: both tests pass.

- [ ] **Step 5: Commit**

```bash
git add datasci/forest.py tests/test_forest.py
git commit -m "feat(datasci): add forest plot for regression results"
```

---

## Task 1.16: `datasci/consort.py` — `plot_consort_flow`

**Files:**
- Create: `datasci/consort.py`
- Create: `tests/test_consort.py`

**Source:** `../ctsi-mao/utils/viz_utils.py` lines 59–160.

**Genericization:** Remove all hardcoded study-specific labels (e.g., "REDCap Export", "Censored (no screening within 4 yr)", "Screened (event observed)"). Replace with kwargs:
- `title_total: str = "Total Records"`
- `title_eligible: str = "Eligible cohort"`
- `title_analytic: str = "Analytic cohort"`
- `title_event: str = "Event observed"`
- `title_censored: str = "Censored"`
- `dpi: int = 300`

The function takes the same `exclusion_stats` dict shape (with keys `total_records`, `ineligible`, `eligible`, `excluded_missing_index_date` [optional], `final_n`, `events`, `censored`, `ineligibility_reasons` [optional dict]).

- [ ] **Step 1: Write failing test**

Write to `tests/test_consort.py`:

```python
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
```

- [ ] **Step 2: Run to verify failure**

Run: `tests/run.sh tests/test_consort.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement**

Write to `datasci/consort.py`:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "matplotlib>=3.4",
# ]
# ///
"""CONSORT-style patient exclusion flow diagram."""

from typing import Dict, Optional
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def plot_consort_flow(exclusion_stats: Dict,
                      save_path: Optional[str] = None,
                      title_total: str = "Total Records",
                      title_eligible: str = "Eligible cohort",
                      title_analytic: str = "Analytic cohort",
                      title_event: str = "Event observed",
                      title_censored: str = "Censored",
                      dpi: int = 300) -> plt.Figure:
    """Create a CONSORT-style patient exclusion flow diagram.

    `exclusion_stats` keys:
        total_records (int, required)
        ineligible (int, required)
        eligible (int, required)
        excluded_missing_index_date (int, optional — adds a second exclusion row)
        final_n (int, required)
        events (int, required)
        censored (int, required)
        ineligibility_reasons (Dict[str, int], optional — itemizes ineligible counts)
    """
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')

    box_props = dict(boxstyle='round,pad=0.4', facecolor='#e8f0fe', edgecolor='#333', linewidth=1.5)
    excl_props = dict(boxstyle='round,pad=0.4', facecolor='#fce8e8', edgecolor='#999', linewidth=1)
    arrow_props = dict(arrowstyle='->', color='#333', linewidth=1.5)

    total = exclusion_stats['total_records']
    ineligible = exclusion_stats['ineligible']
    eligible = exclusion_stats['eligible']
    excluded_index = exclusion_stats.get('excluded_missing_index_date', 0)
    final_n = exclusion_stats['final_n']
    events = exclusion_stats['events']
    censored = exclusion_stats['censored']
    reasons = exclusion_stats.get('ineligibility_reasons', {})

    cx = 3.5

    ax.text(cx, 9.2, f"{title_total}\nN = {total}", ha='center', va='center',
            fontsize=12, fontweight='bold', bbox=box_props)
    ax.annotate('', xy=(cx, 8.5), xytext=(cx, 8.8), arrowprops=arrow_props)

    ax.text(cx, 8.1, f"Assessed for eligibility\nN = {total}", ha='center', va='center',
            fontsize=11, bbox=box_props)
    ax.annotate('', xy=(cx, 7.1), xytext=(cx, 7.6), arrowprops=arrow_props)
    ax.annotate('', xy=(7, 7.8), xytext=(cx + 1.2, 7.8), arrowprops=arrow_props)

    reason_lines = [f"Ineligible (n = {ineligible})"]
    for reason, count in sorted(reasons.items(), key=lambda x: -x[1]):
        reason_lines.append(f"  • {reason}: {count}")
    ax.text(7.2, 7.8, "\n".join(reason_lines), ha='left', va='center',
            fontsize=9, bbox=excl_props)

    ax.text(cx, 6.7, f"{title_eligible}\nN = {eligible}", ha='center', va='center',
            fontsize=12, fontweight='bold', bbox=box_props)

    if excluded_index > 0:
        ax.annotate('', xy=(cx, 5.7), xytext=(cx, 6.2), arrowprops=arrow_props)
        ax.annotate('', xy=(7, 6.4), xytext=(cx + 1.2, 6.4), arrowprops=arrow_props)
        ax.text(7.2, 6.4, f"Excluded: missing index date\nn = {excluded_index}",
                ha='left', va='center', fontsize=9, bbox=excl_props)
        ax.text(cx, 5.3, f"{title_analytic}\nN = {final_n}", ha='center', va='center',
                fontsize=12, fontweight='bold', bbox=box_props)
        outcome_y = 4.3
        arrow_from = 4.8
    else:
        outcome_y = 5.3
        arrow_from = 6.2

    ax.annotate('', xy=(cx, outcome_y + 0.5), xytext=(cx, arrow_from), arrowprops=arrow_props)

    lx, rx = 1.8, 5.2
    ax.annotate('', xy=(lx, outcome_y - 0.2), xytext=(cx, outcome_y + 0.3), arrowprops=arrow_props)
    ax.annotate('', xy=(rx, outcome_y - 0.2), xytext=(cx, outcome_y + 0.3), arrowprops=arrow_props)

    event_props = dict(boxstyle='round,pad=0.4', facecolor='#e8fee8', edgecolor='#333', linewidth=1.5)
    censor_props = dict(boxstyle='round,pad=0.4', facecolor='#fff3e0', edgecolor='#333', linewidth=1.5)

    ax.text(lx, outcome_y - 0.7,
            f"{title_event}\nn = {events} ({events/final_n*100:.1f}%)",
            ha='center', va='center', fontsize=11, fontweight='bold', bbox=event_props)
    ax.text(rx, outcome_y - 0.7,
            f"{title_censored}\nn = {censored} ({censored/final_n*100:.1f}%)",
            ha='center', va='center', fontsize=11, fontweight='bold', bbox=censor_props)

    fig.suptitle("Patient Exclusion Flow", fontsize=14, fontweight='bold', y=0.98)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    if save_path:
        fig.savefig(save_path, dpi=dpi, bbox_inches='tight')
        plt.close(fig)
    return fig
```

- [ ] **Step 4: Run to verify pass**

Run: `tests/run.sh tests/test_consort.py -v`
Expected: both tests pass.

- [ ] **Step 5: Commit**

```bash
git add datasci/consort.py tests/test_consort.py
git commit -m "feat(datasci): add CONSORT flow diagram (genericized labels)"
```

---

## Task 1.17: Run the whole datasci test suite

Sanity check that nothing regressed across files (especially the intra-package imports).

- [ ] **Step 1: Run all datasci tests**

Run: `tests/run.sh tests/ -v`
Expected: all tests pass (approx 30 tests).

- [ ] **Step 2: No commit needed — this is a verification step.**

If failures, debug before proceeding to Phase 2.

---

# Phase 2: `11ty-base/` scaffolding

The shared 11ty baseline. After this phase, a fresh project that copies the contents of `11ty-base/` to its root + runs `npm install` should serve immediately via `npx @11ty/eleventy --serve`.

## Task 2.1: Create `11ty-base/` files

**Files:**
- Create: `11ty-base/.eleventy.js`
- Create: `11ty-base/.eleventyignore`
- Create: `11ty-base/package.json`
- Create: `11ty-base/_includes/base.njk`
- Create: `11ty-base/_includes/sidebar.njk`
- Create: `11ty-base/_data/nav.js`
- Create: `11ty-base/css/main.css` (copy from `../ctsi-mao/css/main.css`)
- Create: `11ty-base/css/prism-dark.css` (copy from `../ctsi-mao/css/prism-dark.css`)
- Create: `11ty-base/README.md`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p 11ty-base/_includes 11ty-base/_data 11ty-base/css
```

- [ ] **Step 2: Create `11ty-base/.eleventy.js`** (the shared baseline — common parts of both source repos, no project-specific transforms)

```javascript
const syntaxHighlight = require("@11ty/eleventy-plugin-syntaxhighlight");
const markdownIt = require("markdown-it");
const markdownItTaskLists = require("markdown-it-task-lists");
const markdownItCallouts = require("markdown-it-obsidian-callouts");

module.exports = function (eleventyConfig) {
  eleventyConfig.addPlugin(syntaxHighlight);

  const md = markdownIt({ html: true, linkify: true, typographer: true })
    .use(markdownItTaskLists)
    .use(markdownItCallouts);
  eleventyConfig.setLibrary("md", md);

  eleventyConfig.addPassthroughCopy("css");

  eleventyConfig.addWatchTarget("_includes/");
  eleventyConfig.addWatchTarget("css/");

  return {
    dir: { input: ".", output: "_site", includes: "_includes", data: "_data" },
    markdownTemplateEngine: "njk",
    pathPrefix: process.env.ELEVENTY_PATH_PREFIX || "/",
  };
};
```

- [ ] **Step 3: Create `11ty-base/.eleventyignore`**

```
node_modules
_site
.venv
README.md
CLAUDE.md
```

- [ ] **Step 4: Create `11ty-base/package.json`**

```json
{
  "name": "11ty-site",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "start": "npx @11ty/eleventy --serve",
    "build": "npx @11ty/eleventy",
    "build:ghpages": "npx @11ty/eleventy --pathprefix=/<PATHPREFIX>"
  },
  "devDependencies": {
    "@11ty/eleventy": "^3.1.2",
    "@11ty/eleventy-plugin-syntaxhighlight": "^5.0.2",
    "markdown-it-obsidian-callouts": "^0.3.3",
    "markdown-it-task-lists": "^2.1.1"
  }
}
```

Note: `<PATHPREFIX>` is a literal token the consumer replaces with their repo name when deploying to GitHub Pages (e.g., `my-site`).

- [ ] **Step 5: Create `11ty-base/_includes/base.njk`**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ title or nav.project or "Site" }}</title>
  <link rel="stylesheet" href="{{ '/css/prism-dark.css' | url }}">
  <link rel="stylesheet" href="{{ '/css/main.css' | url }}">
</head>
<body>
  {% include "sidebar.njk" %}
  <main class="main-content">
    <div class="content">
      {{ content | safe }}
    </div>
  </main>
</body>
</html>
```

- [ ] **Step 6: Create `11ty-base/_includes/sidebar.njk`** (genericized — loops over `nav.sections`)

```html
<button class="nav-toggle" onclick="document.body.classList.toggle('nav-hidden')" aria-label="Toggle navigation"><span></span></button>
<nav class="sidebar">
  <div class="logo">{{ nav.project }}</div>

  {%- for section in nav.sections %}
  <div class="nav-section">
    <h3>{{ section.title }}</h3>
    {%- for item in section.items %}
    <a class="nav-link{% if page.url == item.url %} active{% endif %}" href="{{ item.url | url }}">{{ item.label }}</a>
    {%- endfor %}
  </div>
  {%- endfor %}
</nav>
```

- [ ] **Step 7: Create `11ty-base/_data/nav.js`** (placeholder showing the expected shape)

```javascript
module.exports = {
  project: "Your project",
  sections: [
    {
      title: "Pages",
      items: [
        // { url: "/", label: "Home" },
      ],
    },
  ],
};
```

- [ ] **Step 8: Copy CSS files from `../ctsi-mao/`**

```bash
cp ../ctsi-mao/css/main.css 11ty-base/css/main.css
cp ../ctsi-mao/css/prism-dark.css 11ty-base/css/prism-dark.css
```

- [ ] **Step 9: Create `11ty-base/README.md`**

```markdown
# 11ty baseline

A minimal shared Eleventy 3.x scaffold. After installing into a project root:

1. `npm install`
2. Edit `_data/nav.js` — set `project` and populate `sections`.
3. Add markdown files at the project root or in subdirs. They render through `_includes/base.njk`.
4. `npm start` for local dev; `npm run build` to produce `_site/`.

## Customization points

- **Navigation** — `_data/nav.js`. Each entry in `sections` is `{title, items: [{url, label}]}`.
- **Styles** — `css/main.css` and `css/prism-dark.css`. Replace wholesale to restyle.
- **Layout** — `_includes/base.njk` (page chrome) and `_includes/sidebar.njk` (nav rendering).
- **Eleventy config** — add per-project transforms, passthroughs, computed-data blocks in `.eleventy.js`. The baseline only ships markdownIt + plugins + the `css/` passthrough.

## GitHub Pages

The `build:ghpages` script in `package.json` includes a `<PATHPREFIX>` token. Replace with your repo name (e.g., `npx @11ty/eleventy --pathprefix=/my-site`) so links resolve correctly under `https://<user>.github.io/<repo>/`.
```

- [ ] **Step 10: Verify scaffold builds in a clean directory**

```bash
TMPDIR=$(mktemp -d)
cp -r 11ty-base/. "$TMPDIR/"
cd "$TMPDIR"
echo "# Hello" > index.md
npm install --silent
npx @11ty/eleventy
test -f _site/index.html
echo "Build succeeded"
cd -
rm -rf "$TMPDIR"
```

Expected: prints "Build succeeded" — confirms the scaffold produces a working site without errors.

- [ ] **Step 11: Commit**

```bash
git add 11ty-base/
git commit -m "feat(11ty-base): add shared Eleventy 3.x baseline scaffold"
```

---

# Phase 3: Cloudflare Worker

The `shark.badmath.org` Worker serves install.sh at root and 302-redirects everything else to GitHub raw URLs for `christopherseaman/shark-repellent`.

## Task 3.1: Create Worker source

**Files:**
- Create: `cloudflare-worker/worker.js`
- Create: `cloudflare-worker/wrangler.toml`
- Create: `cloudflare-worker/README.md`
- Create: `cloudflare-worker/.gitignore`

- [ ] **Step 1: Create directory**

```bash
mkdir -p cloudflare-worker
```

- [ ] **Step 2: Create `cloudflare-worker/worker.js`**

```javascript
const REPO_RAW_BASE = "https://raw.githubusercontent.com/christopherseaman/shark-repellent/main";

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const path = url.pathname;

    // Root: serve install.sh with shell-script content type
    if (path === "/" || path === "") {
      const upstream = await fetch(`${REPO_RAW_BASE}/install.sh`);
      if (!upstream.ok) {
        return new Response(`Upstream returned ${upstream.status}`, { status: 502 });
      }
      return new Response(upstream.body, {
        status: 200,
        headers: {
          "Content-Type": "text/x-shellscript; charset=utf-8",
          "Cache-Control": "no-cache",
        },
      });
    }

    // Any other path: 302 to raw.githubusercontent.com
    return Response.redirect(`${REPO_RAW_BASE}${path}`, 302);
  },
};
```

- [ ] **Step 3: Create `cloudflare-worker/wrangler.toml`**

```toml
name = "shark"
main = "worker.js"
compatibility_date = "2026-05-15"

routes = [
  { pattern = "shark.badmath.org/*", zone_name = "badmath.org" },
]
```

`account_id` is intentionally omitted — wrangler reads it from `wrangler login`. Add it here only if deploying via CI.

- [ ] **Step 4: Create `cloudflare-worker/.gitignore`**

```
.wrangler/
node_modules/
.dev.vars
```

- [ ] **Step 5: Create `cloudflare-worker/README.md`**

```markdown
# shark.badmath.org Cloudflare Worker

Serves the shark-repellent install script and proxies file paths to GitHub raw.

## Routes

- `GET /` → returns the contents of the repo's `install.sh` as `text/x-shellscript`. Lets `curl -fsSL shark.badmath.org | bash` work without specifying a path.
- `GET /<path>` → 302 redirects to `https://raw.githubusercontent.com/christopherseaman/shark-repellent/main/<path>`.

## Deploy

```bash
npm install -g wrangler   # one-time
wrangler login            # browser-based auth
wrangler deploy
```

DNS: in the Cloudflare dashboard for `badmath.org`, add a CNAME record `shark` → `<your-account>.workers.dev` (or use the Workers Routes UI). The `routes` block in `wrangler.toml` handles the runtime binding once DNS resolves.

## Local testing

```bash
wrangler dev                          # serves on http://localhost:8787
curl http://localhost:8787            # should return install.sh body
curl -I http://localhost:8787/datasci/ttest.py   # should be 302 to raw.githubusercontent.com
```
```

- [ ] **Step 6: Verify worker.js parses (no deploy)**

Run: `node --check cloudflare-worker/worker.js`
Expected: no output (clean parse). If `node` not installed, skip — wrangler will catch syntax issues on deploy.

- [ ] **Step 7: Commit**

```bash
git add cloudflare-worker/
git commit -m "feat(worker): add shark.badmath.org Cloudflare Worker"
```

---

# Phase 4: `install.sh` dispatcher

The user-facing entry point. Fetches files from `$SHARK_BASE` (default `https://shark.badmath.org`) based on flags.

## Task 4.1: Create `install.sh`

**Files:**
- Create: `install.sh` (at repo root)

- [ ] **Step 1: Write `install.sh`**

Write to `install.sh`:

```bash
#!/usr/bin/env bash
# shark-repellent installer.
# Usage:
#   curl -fsSL shark.badmath.org | bash                          # defaults
#   curl -fsSL shark.badmath.org | bash -s -- datasci            # one tool
#   curl -fsSL shark.badmath.org | bash -s -- --all
#   curl -fsSL shark.badmath.org | bash -s -- --no-notion datasci
#
# Env:
#   SHARK_BASE  source URL prefix (default: https://shark.badmath.org)

set -euo pipefail

SHARK_BASE="${SHARK_BASE:-https://shark.badmath.org}"
TARGET="$PWD"
FORCE=0
DRY_RUN=0

ALL_TOOLS=(datasci notion-sync 11ty-base)
SELECTED=()
EXCLUDED=()

usage() {
  cat <<'EOF'
Usage: curl -fsSL shark.badmath.org | bash [-s -- [FLAGS] [TOOLS]]

Tools (positional, zero or more):
  datasci       Copy datasci/ python package into ./datasci/
  notion-sync   Copy notion-sync.sh to ./scripts/notion-sync
  11ty-base     Scaffold 11ty baseline into project root

Flags:
  --all         Install all three tools (same as no args today)
  --no-<tool>   Exclude one tool from defaults
  --target DIR  Target directory (default: $PWD)
  --force       Overwrite existing files
  --dry-run     Print actions, don't execute
  -h, --help    Print this help and exit

Defaults (no args): datasci + notion-sync + 11ty-base
EOF
}

# --- arg parsing ---
while (( $# > 0 )); do
  case "$1" in
    --all) SELECTED=("${ALL_TOOLS[@]}"); shift ;;
    --no-datasci|--no-notion-sync|--no-11ty-base)
      EXCLUDED+=("${1#--no-}"); shift ;;
    --no-notion) EXCLUDED+=("notion-sync"); shift ;;
    --target) TARGET="$2"; shift 2 ;;
    --force) FORCE=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    datasci|notion-sync|11ty-base) SELECTED+=("$1"); shift ;;
    *)
      echo "error: unknown argument '$1'" >&2
      usage >&2
      exit 1 ;;
  esac
done

# If no tools explicitly selected, use defaults (all)
if (( ${#SELECTED[@]} == 0 )); then
  SELECTED=("${ALL_TOOLS[@]}")
fi

# Apply exclusions
FINAL=()
for tool in "${SELECTED[@]}"; do
  skip=0
  for excl in "${EXCLUDED[@]:-}"; do
    [[ "$tool" == "$excl" ]] && skip=1
  done
  (( skip == 0 )) && FINAL+=("$tool")
done

if (( ${#FINAL[@]} == 0 )); then
  echo "error: no tools selected after exclusions" >&2
  exit 1
fi

# --- helpers ---
say() { printf '%s\n' "$*"; }
do_or_say() {
  if (( DRY_RUN )); then
    say "DRY-RUN: $*"
  else
    eval "$*"
  fi
}

fetch_file() {
  local src_path="$1"   # e.g. datasci/ttest.py
  local dest_path="$2"  # absolute target
  local url="${SHARK_BASE}/${src_path}"
  if [[ -e "$dest_path" && $FORCE -eq 0 ]]; then
    say "skip (exists): $dest_path"
    return
  fi
  do_or_say "mkdir -p \"$(dirname \"$dest_path\")\""
  do_or_say "curl -fsSL \"$url\" -o \"$dest_path\""
  say "  fetched: $dest_path"
}

# --- per-tool installers ---
install_datasci() {
  say "Installing datasci → $TARGET/datasci/"
  local files=(
    __init__.py
    bar.py
    chisquare.py
    consort.py
    cox.py
    diverging_bar.py
    effect_size.py
    fisher.py
    forest.py
    histogram.py
    km.py
    logrank.py
    pvalues.py
    report.py
    summary.py
    ttest.py
  )
  for f in "${files[@]}"; do
    fetch_file "datasci/$f" "$TARGET/datasci/$f"
  done
}

install_notion_sync() {
  say "Installing notion-sync → $TARGET/scripts/notion-sync"
  fetch_file "notion-sync/notion-sync.sh" "$TARGET/scripts/notion-sync"
  do_or_say "chmod +x \"$TARGET/scripts/notion-sync\""
  say ""
  say "  next steps:"
  say "    1. Install the ntn CLI:    curl -fsSL ntn.dev | bash"
  say "    2. Authenticate:           NOTION_KEYRING=0 ntn login   # on headless boxes"
  say "    3. Set parent page:        export NOTION_SYNC_ROOT=<page-url-or-id>"
}

install_11ty_base() {
  say "Installing 11ty-base → $TARGET/"
  local files=(
    .eleventy.js
    .eleventyignore
    package.json
    _includes/base.njk
    _includes/sidebar.njk
    _data/nav.js
    css/main.css
    css/prism-dark.css
    README.md
  )
  for f in "${files[@]}"; do
    fetch_file "11ty-base/$f" "$TARGET/$f"
  done
  say ""
  say "  next steps:"
  say "    1. cd $TARGET && npm install"
  say "    2. Edit _data/nav.js to set project name + sections"
  say "    3. npm start"
}

# --- dispatch ---
say "shark-repellent installer"
say "  source:  $SHARK_BASE"
say "  target:  $TARGET"
say "  tools:   ${FINAL[*]}"
say ""

for tool in "${FINAL[@]}"; do
  case "$tool" in
    datasci) install_datasci ;;
    notion-sync) install_notion_sync ;;
    11ty-base) install_11ty_base ;;
  esac
  say ""
done

say "Done."
```

`chmod +x install.sh`.

- [ ] **Step 2: Lint with bash -n**

Run: `bash -n install.sh`
Expected: no output (clean parse).

- [ ] **Step 3: Test --help**

Run: `bash install.sh --help`
Expected: prints the usage block, exit 0.

- [ ] **Step 4: Test --dry-run defaults**

Run: `bash install.sh --dry-run --target /tmp/shark-test`
Expected: prints `DRY-RUN: mkdir -p ...` and `DRY-RUN: curl ...` lines for all three tools' files. No actual fetches or files created.

- [ ] **Step 5: Test against local files**

Use the repo itself as the source via a file:// URL won't work for curl reliably, but we can simulate by serving the repo on localhost:

```bash
python3 -m http.server 8000 --directory . &
SERVER_PID=$!
sleep 1
TMPDIR=$(mktemp -d)
SHARK_BASE=http://localhost:8000 bash install.sh --target "$TMPDIR"
test -f "$TMPDIR/datasci/ttest.py"
test -f "$TMPDIR/scripts/notion-sync"
test -x "$TMPDIR/scripts/notion-sync"
test -f "$TMPDIR/.eleventy.js"
test -f "$TMPDIR/css/main.css"
kill $SERVER_PID
rm -rf "$TMPDIR"
echo "Smoke test passed"
```

Expected: ends with "Smoke test passed".

- [ ] **Step 6: Test --no-<tool> exclusion**

```bash
python3 -m http.server 8000 --directory . &
SERVER_PID=$!
sleep 1
TMPDIR=$(mktemp -d)
SHARK_BASE=http://localhost:8000 bash install.sh --target "$TMPDIR" --no-notion
test ! -e "$TMPDIR/scripts/notion-sync"
test -f "$TMPDIR/datasci/ttest.py"
kill $SERVER_PID
rm -rf "$TMPDIR"
echo "Exclusion test passed"
```

Expected: ends with "Exclusion test passed".

- [ ] **Step 7: Test --force overwrite**

```bash
python3 -m http.server 8000 --directory . &
SERVER_PID=$!
sleep 1
TMPDIR=$(mktemp -d)
mkdir -p "$TMPDIR/datasci"
echo "PRE-EXISTING" > "$TMPDIR/datasci/ttest.py"
SHARK_BASE=http://localhost:8000 bash install.sh --target "$TMPDIR" datasci   # should skip
grep -q "PRE-EXISTING" "$TMPDIR/datasci/ttest.py" && echo "skip-without-force: OK"
SHARK_BASE=http://localhost:8000 bash install.sh --target "$TMPDIR" --force datasci  # should overwrite
grep -q "PRE-EXISTING" "$TMPDIR/datasci/ttest.py" && echo "FAIL" || echo "force-overwrite: OK"
kill $SERVER_PID
rm -rf "$TMPDIR"
```

Expected: prints "skip-without-force: OK" and "force-overwrite: OK".

- [ ] **Step 8: Test unknown-tool error**

Run: `bash install.sh --target /tmp not-a-tool 2>&1; echo "exit=$?"`
Expected: prints "error: unknown argument 'not-a-tool'", usage, "exit=1".

- [ ] **Step 9: Commit**

```bash
git add install.sh
git commit -m "feat: add curl|bash installer dispatcher"
```

---

# Phase 5: Cleanup + deletions

## Task 5.1: Delete setuptools/PyPI metadata

**Files:**
- Delete: `setup.py`
- Delete: `MANIFEST.in`
- Delete: `requirements.txt`

- [ ] **Step 1: Remove via git rm**

```bash
git rm setup.py MANIFEST.in requirements.txt
```

- [ ] **Step 2: Verify removed**

Run: `ls setup.py MANIFEST.in requirements.txt 2>&1 || echo "all gone"`
Expected: prints "all gone".

- [ ] **Step 3: Commit**

```bash
git commit -m "chore: drop setuptools metadata (replaced by curl|bash installer)"
```

---

## Task 5.2: Delete empty `reporting/` placeholder

**Files:**
- Delete: `reporting/report_gen_PLACEHOLDER.py`
- Delete: `reporting/` (empty dir after removal)

- [ ] **Step 1: Remove via git rm**

```bash
git rm reporting/report_gen_PLACEHOLDER.py
rmdir reporting
```

- [ ] **Step 2: Commit**

```bash
git commit -m "chore: remove empty reporting/ placeholder"
```

---

## Task 5.3: Delete `viztools/` (now superseded by `datasci/diverging_bar.py`)

**Files:**
- Delete: `viztools/__init__.py`
- Delete: `viztools/` (empty after removal — `charts.py` already moved in Task 1.9)

- [ ] **Step 1: Confirm only `__init__.py` remains**

Run: `ls viztools/`
Expected: just `__init__.py` (possibly a `__pycache__/`).

- [ ] **Step 2: Remove**

```bash
git rm viztools/__init__.py
rm -rf viztools/__pycache__   # if present
rmdir viztools
```

- [ ] **Step 3: Commit**

```bash
git commit -m "chore: remove viztools/ (superseded by datasci/diverging_bar.py)"
```

---

## Task 5.4: Rewrite root `README.md`

**Files:**
- Modify: `README.md` (full rewrite — old content described the viztools-only package)

- [ ] **Step 1: Replace `README.md` contents**

Write to `README.md`:

```markdown
# shark-repellent

A personal collection of project tools. Each subdirectory is a standalone toolkit.

## Install

```bash
curl -fsSL shark.badmath.org | bash
```

Defaults install `datasci/` + `notion-sync` + `11ty-base/` into the current directory. Run with `--help` for flags.

## Tools

- **`datasci/`** — Python utilities for analysis/reporting: charts, markdown reports, stats primitives (t-test, chi-square, summary, effect size), survival analysis (KM, Cox, log-rank, forest, CONSORT). One file per concern, each with a PEP 723 dep header for `uv run`.
- **`notion-sync/`** — bash wrapper around the `ntn` CLI for pushing markdown to a Notion root page.
- **`11ty-base/`** — Eleventy 3.x scaffold (config, layout, sidebar, CSS) for project sites.
- **`firefox_autoconfig/`** — Firefox autoconfig that disables Private Browsing (machine config, not installed via the dispatcher).
- **`cloudflare-worker/`** — Worker code for `shark.badmath.org`.

See per-subdir READMEs for details. Repo-level guidance for contributors / future Claude instances is in `CLAUDE.md`.

## License

MIT — see `LICENSE`.
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: rewrite README for restructured repo"
```

---

# Phase 6: Update `CLAUDE.md`

The CLAUDE.md currently describes the four-toolkit world with `viztools/`. After the restructure it needs to describe the six-unit world with `datasci/`.

## Task 6.1: Rewrite `CLAUDE.md`

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Read current CLAUDE.md**

Run: `cat CLAUDE.md`
This is needed so the rewrite preserves the conventions the user values and reuses the structure they liked (toolkit table, working-in-X sections, conventions list).

- [ ] **Step 2: Rewrite to reflect the new structure**

Write to `CLAUDE.md`:

```markdown
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A personal collection of project tools. Each top-level subdirectory is a standalone toolkit with its own language, runtime, and lifecycle. The `install.sh` dispatcher + `shark.badmath.org` Cloudflare Worker make tools `curl | bash`-installable into consumer projects.

## The six units

| Subdir / file | Stack | What it is |
| --- | --- | --- |
| `datasci/` | Python 3.11+ (PEP 723 inline metadata) | 15 single-purpose files for analysis/reporting: charts, markdown report builders, stats primitives (t-test, chi-square, Fisher, summary, effect size, p-value format), KM/Cox/log-rank/forest/CONSORT for survival. Each file declares its own deps in a `# /// script` header; heavy deps (lifelines) are lazy-imported inside function bodies. |
| `11ty-base/` | Node + Eleventy 3.x | Shared static-site scaffold: `.eleventy.js`, `_includes/base.njk` + genericized `sidebar.njk`, `_data/nav.js` placeholder, `css/main.css` + `prism-dark.css`. Driven by a `nav.sections` array — no hardcoded section names. |
| `notion-sync/` | Bash + `ntn` CLI + jq | Push/pull markdown to Notion via `ntn`. Tracks page IDs in a `.notion-sync.tsv` sidecar in the consumer project. |
| `firefox_autoconfig/` | Firefox Autoconfig JS | Disables Private Browsing UI + `Tools:PrivateBrowsing` command. Machine-config artifact — not installed via the dispatcher. |
| `cloudflare-worker/` | JavaScript (Workers runtime) | `shark.badmath.org` Worker: serves `install.sh` at `/`, 302-redirects everything else to GitHub raw. |
| `install.sh` (root) | Bash | The dispatcher — fetches files from `$SHARK_BASE` (default `https://shark.badmath.org`) per-tool. |

## Running the tools

**`datasci/`** — each file is `uv run`-able standalone (PEP 723 resolves deps). For import use, a consumer's calling script lists the same deps in *its* PEP 723 block, then `from datasci.<module> import <fn>`. Example:

```bash
uv run --with pandas --with scipy python -c "
from datasci.ttest import perform_t_test
import pandas as pd
print(perform_t_test(pd.Series([1,2,3]), pd.Series([4,5,6])))
"
```

Intra-`datasci/` imports: `report.py` and `km.py` both depend on `pvalues.py`. The installer always vendors the whole `datasci/` directory as a unit, so this works; do not inline `format_p_value` into multiple files.

**Tests** — `tests/run.sh` wraps `uv run pytest` with the union of deps. Run a single test: `tests/run.sh tests/test_ttest.py -v`.

**`11ty-base/`** — installed into a consumer project root: `npm install && npm start`. See `11ty-base/README.md` for the customization points (`_data/nav.js`, CSS files, per-project transforms in `.eleventy.js`).

**`notion-sync/`** — see `notion-sync/sync-workflow.md` (reference workflow) and `notion-sync/obsidian-to-enhanced-markdown.md` (Enhanced Markdown translation table verified against `ntn 0.14.0`). Requires `NOTION_KEYRING=0` on headless boxes and `NOTION_SYNC_ROOT` env var for the default parent page. `ntn` itself installs via `curl -fsSL ntn.dev | bash`.

**`firefox_autoconfig/`** — not "run"; deployed. See `firefox_autoconfig/place_in_firefox_contents_resources.md` for placement + debugging notes (Browser Toolbox, `Cu.reportError` output in Browser Console, current element IDs).

**`cloudflare-worker/`** — deploy with `wrangler deploy` after `wrangler login`. See `cloudflare-worker/README.md`. Local test via `wrangler dev`.

**`install.sh`** — `bash install.sh --help` for flags. Test against a local source: `python3 -m http.server 8000 --directory . & SHARK_BASE=http://localhost:8000 bash install.sh --target /tmp/x`.

## When working in `datasci/`

- Files name themselves by **what they do**, not by academic category. Don't introduce `stats.py` or `viz.py` — keep the single-concern-per-file pattern (`ttest.py`, `histogram.py`, `km.py`, etc.).
- Heavy deps (`lifelines`, anything beyond numpy/pandas/matplotlib/scipy) are **lazy-imported inside functions**, so `import datasci.km` doesn't drag `lifelines` into the importer's env.
- Each file has a PEP 723 header listing only its own deps. When adding a new module, update the header to match the actual imports.
- Tests live in `tests/test_<module>.py`. Use the toy-data smoke-test pattern (build minimal pandas frames, call the function, assert structural properties of the result). Don't mock the underlying math.
- The orchestrator pattern from ctsi-mao (config-driven report dispatch) is **not** part of `datasci/` — it lives in consumer projects.

## When working in `11ty-base/`

- The sidebar is **generic** — driven by `nav.sections = [{title, items}, ...]` from `_data/nav.js`. Do not hardcode section names in `sidebar.njk`.
- `.eleventy.js` deliberately ships only the shared baseline (plugins, markdownIt, dir, pathPrefix). Per-project transforms / passthroughs / computed-data blocks belong in the consumer's own `.eleventy.js`, not here.
- CSS is externalized into `css/main.css` + `css/prism-dark.css` (linked from `base.njk`). Don't inline a `<style>` block into the layout.

## When working in `notion-sync/`

- The two `.md` files are reference material verified against `ntn 0.14.0`: `sync-workflow.md` documents the helper's workflow, `obsidian-to-enhanced-markdown.md` is the Enhanced Markdown translation table.
- The `upload` subcommand auto-renames code/config extensions (`.py`, `.sh`, etc.) to `.txt` because Notion's File Upload API rejects those with `400 validation_error`. Preserve that workaround.
- `ntn pages update` replaces page content and refuses to orphan child pages. The helper deliberately does **not** expose `--allow-deleting-content` (destructive).

## When working in `firefox_autoconfig/`

- Firefox UI element IDs change between versions. Current targets: `Tools:PrivateBrowsing` (command), `key_privatebrowsing`, `menu_newPrivateWindow`, `appMenu-private-window-button`, `context-openlinkprivate`. Use the Browser Toolbox to find new IDs when they move.
- The script disables the `<command>` element rather than only hiding triggers — that neutralizes menu items + keyboard shortcuts in one shot. Keep that pattern.
- Use `Cu.reportError(...)` for logging; output appears in the Browser Console.

## When working in `cloudflare-worker/`

- The GitHub repo path (`christopherseaman/shark-repellent`) is hardcoded in `worker.js`. This is intentional — personal-use, no need to parameterize.
- `wrangler.toml` omits `account_id`; wrangler reads it from `wrangler login`. Add it explicitly only if deploying from CI.

## Repo conventions

- **No co-authored-by / attribution tags** in commits.
- **Conventional commit style** (`feat:`, `fix:`, `docs:`, `chore:`).
- **`uv` over `pip`/`venv`** for any Python work. Standalone scripts and `datasci/` modules use PEP 723 inline metadata.
- **No new docs proactively** — the existing per-subdir READMEs (`notion-sync/sync-workflow.md`, `firefox_autoconfig/place_in_firefox_contents_resources.md`, `11ty-base/README.md`, `cloudflare-worker/README.md`) are deliberate. Don't add others without being asked.
- **Tests via `tests/run.sh`** (wraps `uv run pytest` with deps `--with`-ed inline). The repo has no committed virtualenv or installed-package state.
```

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(claude-md): rewrite for restructured repo"
```

---

# Phase 7: Final verification

## Task 7.1: End-to-end installer smoke test

- [ ] **Step 1: Run the installer against a tmp dir using local files**

```bash
python3 -m http.server 8000 --directory . &
SERVER_PID=$!
sleep 1
TMPDIR=$(mktemp -d)
SHARK_BASE=http://localhost:8000 bash install.sh --target "$TMPDIR"
# Verify expected artifacts:
test -f "$TMPDIR/datasci/__init__.py"
test -f "$TMPDIR/datasci/ttest.py"
test -f "$TMPDIR/datasci/km.py"
test -f "$TMPDIR/datasci/report.py"
test -f "$TMPDIR/scripts/notion-sync"
test -x "$TMPDIR/scripts/notion-sync"
test -f "$TMPDIR/.eleventy.js"
test -f "$TMPDIR/_includes/base.njk"
test -f "$TMPDIR/_data/nav.js"
test -f "$TMPDIR/css/main.css"
kill $SERVER_PID
rm -rf "$TMPDIR"
echo "End-to-end installer test PASSED"
```

Expected: prints "End-to-end installer test PASSED" with no failed assertions.

- [ ] **Step 2: Verify datasci tests still pass**

Run: `tests/run.sh tests/ -v`
Expected: all tests pass (approx 30 tests, no regressions from the file moves/edits above).

- [ ] **Step 3: Verify git state is clean**

Run: `git status`
Expected: "nothing to commit, working tree clean" (assuming all per-task commits have been made).

- [ ] **Step 4: Print summary**

Run: `git log --oneline main..HEAD | head -40`
Expected: ~25–30 commits spanning Phases 0–6, each focused on one task. Sanity-check the commit messages for consistency.

---

## Open items intentionally NOT in this plan

- **Cloudflare Worker deployment.** `wrangler deploy` requires browser-based `wrangler login` — interactive, not automatable from this plan. The user will deploy the Worker manually after the file changes land, then point `shark.badmath.org` DNS at it.
- **First `git push`.** Until the worker is live, `curl shark.badmath.org` won't resolve. The repo lands on `main` first; deploy + DNS happens after.
- **Migrating `../ctsi-mao` and `../datasci_223` to consume from `shark.badmath.org`.** Out of scope per the spec; future work once the baseline proves out.
