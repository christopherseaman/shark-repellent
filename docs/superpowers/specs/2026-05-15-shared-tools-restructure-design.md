# Shared-tools restructure design

**Date:** 2026-05-15

## Context

`shark-repellent` is a personal collection of tools the owner reuses across consulting projects. It currently holds four loosely-related subdirs (`viztools/`, `firefox_autoconfig/`, `notion-sync/`, an empty `reporting/` placeholder) plus repo-root setuptools metadata leftover from when viztools was the only tool.

This restructure does three things:

1. Brings in two more toolkits from sibling repos: the shared 11ty static-site baseline used by `../datasci_223` and `../ctsi-mao`, and the project-agnostic Python utilities from `../ctsi-mao/utils/`.
2. Combines viztools' single chart function with the imported Python utilities into a single `datasci/` package, organized as one file per concern.
3. Replaces the setuptools install model with a `curl | bash` installer dispatched via `shark.badmath.org` (Cloudflare Worker fronting GitHub raw URLs).

## Goals

- One umbrella install command (`curl -fsSL shark.badmath.org | bash`) places sensible default tools into a target project.
- Per-tool selection via positional args; per-tool exclusion via `--no-<tool>`.
- Each Python file is self-describing (PEP 723 header) so it is `uv run`-able standalone and import-friendly when its calling script lists deps.
- Heavy deps (lifelines, scipy) are lazy-imported inside functions so `import datasci.km` does not force-load `lifelines`.
- Each tool subdir is self-contained: notion-sync stays bash, 11ty-base stays JS/Nunjucks, datasci stays Python. No cross-tool dependencies.
- Files name themselves by what they *do* (specific method/test/output), not by the academic category they belong to.

## Non-goals

- Versioning. Files always come from `main`. Tag-based versioning can be added by parameterizing the Worker later if needed.
- Distribution to third parties. The installer is for the owner's projects.
- Restructuring `firefox_autoconfig`. Stays in the repo as a reference, **not** part of the installer (it's machine config, not project tooling).
- Extracting the survival reports themselves (the `rpt_NN_*.py` files from ctsi-mao). Those are project-specific and stay in ctsi-mao.

## Tools after restructure

| Subdir / file | Purpose | In installer? |
|---|---|---|
| `datasci/` | Python utilities, 15 single-purpose files | Yes (default) |
| `notion-sync/` | bash wrapper around `ntn` CLI (unchanged) | Yes (default) |
| `11ty-base/` | shared 11ty baseline scaffolding | Yes (default) |
| `firefox_autoconfig/` | Firefox lockdown autoconfig (unchanged) | **No** |
| `cloudflare-worker/` | Worker code + wrangler config for `shark.badmath.org` | **No** (deployed separately via `wrangler`) |
| `install.sh` (root) | Dispatcher script | n/a — it *is* the installer |

## `datasci/` inventory

One file per concern. Each file starts with a PEP 723 header listing only the deps that file uses.

| File | Functions | PEP 723 deps |
|---|---|---|
| `__init__.py` | (empty — package marker only) | — |
| `diverging_bar.py` | `create_diverging_bar_chart` | numpy, pandas, matplotlib |
| `histogram.py` | `create_histogram` (with optional cutpoint annotation) | matplotlib, pandas, numpy |
| `bar.py` | `create_bar_plot` | matplotlib, numpy |
| `report.py` | `create_markdown_section`, `save_markdown_report`, `generate_report`, `format_statistical_results`, `_ensure_table_spacing` | pandas |
| `ttest.py` | `perform_t_test` | scipy, numpy, pandas |
| `chisquare.py` | `perform_chi_square` (falls back to `scipy.stats.fisher_exact` internally for sparse 2x2) | scipy, numpy, pandas |
| `fisher.py` | `fishers_exact_test` (standalone) | scipy, pandas |
| `summary.py` | `calculate_summary_stats` | pandas |
| `effect_size.py` | `calculate_effect_size` (Cohen's d) | numpy, pandas |
| `pvalues.py` | `format_p_value`, `is_significant` | pandas |
| `km.py` | `fit_km`, `fit_km_by_group`, `km_at_timepoints`, `plot_km`, `plot_loglog` | pandas, numpy, matplotlib, lifelines (lazy) |
| `cox.py` | `fit_cox_univariate`, `fit_cox_multivariable`, `cox_summary_table`, `check_proportional_hazards` | pandas, numpy, lifelines (lazy) |
| `logrank.py` | `perform_logrank` | pandas, numpy, lifelines (lazy) |
| `forest.py` | `plot_forest` | matplotlib, pandas, numpy |
| `consort.py` | `plot_consort_flow` | matplotlib |

### Source mapping

| Destination | Source |
|---|---|
| `diverging_bar.py` | `viztools/charts.py` (current repo) — move as-is |
| `report.py` | `../ctsi-mao/utils/reporting.py` — move as-is (file renamed to `report.py`) |
| `ttest.py`, `chisquare.py`, `fisher.py`, `summary.py`, `effect_size.py`, `pvalues.py` | `../ctsi-mao/utils/stats_utils.py` — extract per-function |
| `histogram.py`, `bar.py` | `../ctsi-mao/utils/viz_utils.py` — extract; remove `PLOT_SETTINGS` config dependency (function kwargs with defaults instead) |
| `km.py`, `cox.py`, `logrank.py`, `forest.py`, `consort.py` | `../ctsi-mao/utils/{stats_utils,viz_utils}.py` — extract survival functions; remove `PLOT_SETTINGS` dependency |

### Genericization rules

When extracting from ctsi-mao:

- `PLOT_SETTINGS` reads become **function kwargs with sensible defaults** matching ctsi-mao's values: `dpi=300`, `figsize=(8,6)`, `style='whitegrid'`. `km_colors`, `forest_color`, and CONSORT box colors become explicit args.
- `_build_color_map`'s LEP/non-LEP color logic is dropped; the generic version uses matplotlib's default cycle, with optional `color_map={'group_label': '#xxx'}` override arg.
- `_save_fig` is inlined per file rather than shared (avoids re-introducing cross-file deps for trivial logic).
- All `import lifelines` calls stay inside function bodies (already lazy in source).

### Intra-`datasci/` imports

Some files import from siblings within `datasci/`:

- `report.py` → `pvalues.py` (uses `format_p_value` inside `format_statistical_results`).
- `km.py` → `pvalues.py` (uses `format_p_value` for log-rank p annotation inside `plot_km`).

These are fine — the installer always vendors the whole `datasci/` directory as a unit. Do *not* inline `format_p_value` into both call sites: it would duplicate formatting rules and drift over time.

### Per-file PEP 723 header shape

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "numpy>=1.20",
#   "pandas>=1.3",
# ]
# ///
"""Module docstring."""
```

`uv run datasci/ttest.py` then resolves only the deps that module needs. Consumers `import datasci.ttest` from their own uv-managed scripts, listing matching deps in their own PEP 723 block.

## `11ty-base/` inventory

| File | Notes |
|---|---|
| `.eleventy.js` | Common parts of both source repos: `syntaxHighlight` plugin, `markdownIt` + task-lists + obsidian-callouts, `dir` config, env-driven `pathPrefix`, `addWatchTarget("_includes/")`. **No** project-specific transforms, passthroughs, or computed-data blocks. |
| `.eleventyignore` | Minimal: `node_modules`, `_site`, `.venv`. |
| `package.json` | Scripts: `start` / `build` / `build:ghpages`. The `build:ghpages` script contains a literal `<PATHPREFIX>` token the project owner replaces with their repo name. devDependencies: `@11ty/eleventy ^3.1.2`, `@11ty/eleventy-plugin-syntaxhighlight ^5.0.2`, `markdown-it-obsidian-callouts ^0.3.3`, `markdown-it-task-lists ^2.1.1`. |
| `_includes/base.njk` | ctsi-mao's version (externalized CSS links — no inline `<style>` block). |
| `_includes/sidebar.njk` | **Genericized** — loops over `nav.sections = [{title, items: [{url, label}]}, ...]` instead of hardcoded "Study/Reports/Communications" or "Resources/Lectures". |
| `_data/nav.js` | Placeholder showing the shape: `{ project: "Your project", sections: [{title: "Pages", items: []}] }`. |
| `css/main.css` | ctsi-mao's verbatim (343 lines). |
| `css/prism-dark.css` | ctsi-mao's verbatim (106 lines). |
| `README.md` | Short doc covering customization points: edit `_data/nav.js` for nav, replace `css/main.css` to restyle, add own `.eleventy.js` transforms/passthroughs for project-specific routing. |

After install, `npx @11ty/eleventy --serve` works immediately (after `npm install`). Customization is additive.

## `install.sh` design

### CLI

```
Usage: curl -fsSL shark.badmath.org | bash [-s -- [FLAGS] [TOOLS]]

Tools (positional, zero or more):
  datasci       Vendor datasci/ python package into ./datasci/
  notion-sync   Copy notion-sync.sh to ./scripts/notion-sync
  11ty-base     Scaffold 11ty baseline into project root

Flags:
  --all         Install all three tools (same as no args today)
  --no-<tool>   Exclude one tool from defaults
  --target DIR  Target directory (default: $PWD)
  --force       Overwrite existing files
  --dry-run     Print actions, don't execute
  -h, --help    Print usage and exit

Defaults (no positional args, no flags): datasci + notion-sync + 11ty-base
```

### Behavior

- Each per-tool action is a bash function (`install_datasci`, `install_notion_sync`, `install_11ty_base`).
- File downloads via `curl -fsSL "$SHARK_BASE/<path>"` (env var, default `https://shark.badmath.org`). This makes it trivial to point at a fork or test branch.
- Per-file check: if target file exists and `--force` not set, skip with a warning. Print summary at end of which files were placed/skipped.
- Network failure during a fetch: print the failed URL and curl's exit code, exit non-zero. Files already placed remain in place (partial install is fine — re-running fills the gaps).
- Unknown tool name: print usage and exit non-zero.
- `--dry-run` prints the curl commands that would run; touches no files.
- Re-running on a clean target reinstalls cleanly. Re-running on a populated target skips existing files (warning) unless `--force`.

### Per-tool install actions

- **datasci**: `mkdir -p $TARGET/datasci`, then fetch each `.py` file from `$SHARK_BASE/datasci/` into `$TARGET/datasci/`.
- **notion-sync**: `mkdir -p $TARGET/scripts`, fetch `notion-sync.sh` → `$TARGET/scripts/notion-sync`, `chmod +x`. Print one-line hint about setting `NOTION_SYNC_ROOT` and installing the `ntn` CLI (`curl -fsSL ntn.dev | bash`).
- **11ty-base**: fetch `.eleventy.js`, `.eleventyignore`, `package.json` into `$TARGET/`; `_includes/base.njk` + `_includes/sidebar.njk` into `$TARGET/_includes/`; `_data/nav.js` into `$TARGET/_data/`; `css/main.css` + `css/prism-dark.css` into `$TARGET/css/`.

## Cloudflare Worker

`cloudflare-worker/worker.js`:

- `GET /` → fetch `https://raw.githubusercontent.com/christopherseaman/shark-repellent/main/install.sh` and return its body with `Content-Type: text/x-shellscript`. (Lets `curl shark.badmath.org | bash` work without `/install.sh`.)
- `GET /<path>` → 302 redirect to `https://raw.githubusercontent.com/christopherseaman/shark-repellent/main/<path>`.
- Repo path is hardcoded in the Worker; this is personal-use, no need to parameterize.

`cloudflare-worker/wrangler.toml`: minimal config — `name = "shark"`, route `shark.badmath.org/*`, current `compatibility_date`. `account_id` is left out of the committed file (read from `wrangler login`).

`cloudflare-worker/README.md`: short deploy doc covering `wrangler login` → `wrangler deploy`, the DNS-side step of pointing `shark.badmath.org` at the Worker (Cloudflare dashboard), and how to test locally via `wrangler dev`.

## Deletions

- `setup.py`
- `MANIFEST.in`
- root `requirements.txt`
- `viztools/` (contents move to `datasci/diverging_bar.py`; the `__init__.py` is removed because `datasci/__init__.py` takes its place)
- `reporting/` placeholder directory
- The current root `README.md` is rewritten (currently only documents viztools' aspirational API).

## Out of scope

- Tag-based versioning of the Worker. (Future work; add a `?ref=` query param later if needed.)
- An `update` subcommand for the installer. (Re-run the installer to update.)
- Extracting further functions from ctsi-mao. (Future, on-demand.)
- Migrating consumers (`../datasci_223`, `../ctsi-mao`) to fetch their 11ty baseline from `shark.badmath.org`. (Future, once 11ty-base proves out here.)

## Testing approach

- **Installer**: run against a tmp dir and assert expected files land. Cover: defaults, single-tool, `--all`, `--no-<tool>`, `--force`, `--dry-run`, unknown tool, existing-file skip, network failure (e.g., set `SHARK_BASE` to an unreachable host).
- **Each `datasci/*.py` file**: `uv run datasci/<file>.py --help` should resolve PEP 723 deps and import without error. For files with public-API entry points, a `__main__` block that runs a minimal smoke case is acceptable.
- **`diverging_bar.py` smoke test** already verified during the prior viztools rename — should still pass after move into `datasci/`.
- **Cloudflare Worker**: `wrangler dev` locally, `curl localhost:8787` returns `install.sh`, `curl localhost:8787/datasci/ttest.py` 302s to the raw URL.

## Open questions

None — all design decisions are settled.
