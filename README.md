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
