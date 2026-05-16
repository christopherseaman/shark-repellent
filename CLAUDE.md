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
