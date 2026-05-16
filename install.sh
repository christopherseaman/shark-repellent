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

# run_cmd CMD [ARGS...] — executes or prints the command depending on DRY_RUN
run_cmd() {
  if (( DRY_RUN )); then
    say "DRY-RUN: $*"
  else
    "$@"
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
  run_cmd mkdir -p "$(dirname "$dest_path")"
  run_cmd curl -fsSL "$url" -o "$dest_path"
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
  run_cmd chmod +x "$TARGET/scripts/notion-sync"
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
