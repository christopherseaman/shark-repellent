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
