# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A personal collection of small, independent tools the owner reuses across consulting projects. It is **not** a single package — each top-level subdirectory is a standalone toolkit with its own language, runtime, and install story. Treat them as siblings, not modules of one system. The repo is mid-reorganization; expect rough edges and placeholders.

## The four toolkits

| Subdir | What it is | Stack |
| --- | --- | --- |
| `viztools/` | The originating tool: `charts.create_diverging_bar_chart()` — matplotlib helper for Likert-style diverging bar charts with auto-split neutral category. Installable as the `viztools` Python package (`setup.py` at repo root). | Python (numpy, pandas, matplotlib) |
| `firefox_autoconfig/` | Enterprise-style Firefox lockdown that disables Private Browsing UI and the underlying `Tools:PrivateBrowsing` command. | Firefox Autoconfig (`firefox.cfg` JS + `defaults/pref/autoconfig.js`) |
| `notion-sync/` | `notion-sync.sh` — bash wrapper around the `ntn` CLI for pushing/pulling markdown to a Notion root page, tracking page IDs in a `.notion-sync.tsv` sidecar. | Bash, `ntn` (Notion CLI), `jq` |
| `reporting/` | Empty placeholder (`report_gen_PLACEHOLDER.py` is 0 bytes). Future-work slot. | — |

`viztools` is the originating tool; the rest of the repo grew around it. The Python packaging at the repo root (`setup.py`, `MANIFEST.in`, `requirements.txt`, `README.md`) exists specifically to ship `viztools` — the other three toolkits are not Python packages and are not picked up by `find_packages()`.

## Running things

There is no project-wide build, lint, or test runner. Each toolkit runs on its own:

**`viztools/`** — installable Python package. The README's documented import path works as-is:
```bash
uv pip install -e .   # or: pip install -e .
```
```python
from viztools.charts import create_diverging_bar_chart
```
For ad-hoc execution without installing:
```bash
uv run --with numpy --with pandas --with matplotlib python -c "
from viztools.charts import create_diverging_bar_chart
create_diverging_bar_chart(data={'A': [20,30,10,25,15]}, labels=['SD','D','N','A','SA'], output_path='out.png')
"
```
On headless boxes, set `MPLBACKEND=Agg` to avoid matplotlib trying to open a display.

**`firefox_autoconfig/`** — not "run"; deployed. `firefox.cfg` goes in Firefox's `Contents/Resources/` (macOS) or install root (Linux/Windows); `defaults/pref/autoconfig.js` goes in `Contents/Resources/defaults/pref/`. See `place_in_firefox_contents_resources.md` for the full deployment + debugging notes (Browser Toolbox, `Cu.reportError` output in Browser Console, element-ID research). The cfg's first line **must** be a comment — Firefox skips line 1.

**`notion-sync/notion-sync.sh`** — see `notion-sync/sync-workflow.md` for the full workflow. The TL;DR:
```bash
export NOTION_KEYRING=0                # required on headless / WSL / SSH
export NOTION_SYNC_ROOT=<page-url-or-id>
./notion-sync/notion-sync.sh push report.md      # creates on first push, updates after
./notion-sync/notion-sync.sh pull report.md
./notion-sync/notion-sync.sh upload diagram.png  # auto-renames code/config extensions to .txt
./notion-sync/notion-sync.sh list
```
The sidecar `.notion-sync.tsv` (path → page-id mapping) is the single source of truth for what's tracked; it's plain TSV and intended to be hand-edited when re-pointing or untracking files.

## When working in `notion-sync/`

- The two `.md` files there are **reference material**, not READMEs: `sync-workflow.md` documents the helper's intended workflow and `obsidian-to-enhanced-markdown.md` is an empirically-verified translation table for `ntn 0.14.0`'s Enhanced Markdown format. If a task asks "how does X work in notion-sync", check these before grepping or guessing.
- Notion's File Upload API rejects code/config extensions (`.py`, `.sh`, `.md`, etc.) with `400 validation_error`. The `upload` subcommand works around this by appending `.txt`; preserve that behavior if editing.
- `ntn pages update` **replaces** page content and refuses to orphan child pages — the helper deliberately does not expose `--allow-deleting-content`. Don't add a flag for it without a deliberate ask.

## When working in `firefox_autoconfig/`

- Firefox UI element IDs change between versions. The current script targets `Tools:PrivateBrowsing` (command), `key_privatebrowsing`, `menu_newPrivateWindow`, `appMenu-private-window-button`, `context-openlinkprivate`. If a target moves, find the new ID via the Browser Toolbox (Ctrl+Shift+Alt+I → Settings → Enable Browser Chrome and add-on debugging).
- The script intentionally **disables the `<command>` element** rather than only hiding triggers — disabling the command neutralizes menu items + keyboard shortcuts in one shot. Keep that pattern unless the task explicitly calls for visibility-only changes.
- Use `Cu.reportError(...)` for logging; output appears in the Browser Console. There's no other diagnostic channel.

## Conventions specific to this repo

- **No co-authored-by / attribution tags in commits** (per the owner's global preferences).
- **Conventional commit style** (`feat:`, `fix:`, `docs:`).
- **`uv` over `pip`/`venv`** for any Python work. PEP 723 inline script metadata is preferred for standalone scripts; `requirements.txt` exists but only covers the viz module's deps.
- **Don't add READMEs/docs proactively** — the owner has been deliberate about which subdirs get reference docs (notion-sync, firefox_autoconfig) and which don't.
