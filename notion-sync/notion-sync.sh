#!/usr/bin/env bash
# notion-sync — minimal ntn wrapper for pushing markdown reports to Notion.
# Tracks the Notion page id per file in a .tsv sidecar so subsequent pushes update in place.
#
# Usage:
#   notion-sync push <file.md> [--parent <page-id-or-url>]
#   notion-sync pull <file.md>
#   notion-sync upload <file>           # auto-renames code files to .txt (Notion API quirk)
#   notion-sync list
#
# First-time push of each file needs a parent. Either pass --parent <id-or-url>
# or set NOTION_SYNC_ROOT in your environment (e.g. in .envrc / shell profile).
# Subsequent pushes update in place using the id tracked in .notion-sync.tsv.
#
# Requires: ntn (https://developers.notion.com/cli/get-started/overview), jq.
# Auth: set NOTION_KEYRING=0 if the OS keychain isn't writable (headless / WSL / SSH).

set -euo pipefail

MAP="${NOTION_SYNC_MAP:-.notion-sync.tsv}"   # path\tpage-id, one per line
ROOT="${NOTION_SYNC_ROOT:-}"                  # default parent page id-or-url for first-time pushes

lookup() { [[ -f "$MAP" ]] && awk -F'\t' -v f="$1" '$1 == f { print $2; exit }' "$MAP" || true; }

cmd="${1:-}"; shift || { sed -n '/^# Usage:/,/^$/p' "$0"; exit 1; }

case "$cmd" in
  push)
    file="${1:-}"; shift || { echo "missing file"; exit 1; }
    [[ -f "$file" ]] || { echo "no such file: $file"; exit 1; }
    parent="$ROOT"
    while (( $# > 0 )); do case "$1" in --parent) parent="$2"; shift 2 ;; *) shift ;; esac; done
    id="$(lookup "$file")"
    if [[ -n "$id" ]]; then
      ntn pages update "$id" < "$file" >/dev/null
      echo "updated $file -> $id"
    else
      [[ -n "$parent" ]] || { echo "first push requires --parent <id-or-url> or NOTION_SYNC_ROOT env var"; exit 1; }
      id="$(ntn pages create --parent "page:$parent" --json < "$file" | jq -r .id)"
      printf '%s\t%s\n' "$file" "$id" >> "$MAP"
      echo "created $file -> $id"
    fi
    ;;

  pull)
    file="${1:-}"; shift || { echo "missing file"; exit 1; }
    id="$(lookup "$file")"
    [[ -n "$id" ]] || { echo "$file not tracked in $MAP"; exit 1; }
    ntn pages get "$id" > "$file"
    echo "pulled $id -> $file"
    ;;

  upload)
    src="${1:-}"; [[ -f "$src" ]] || { echo "no such file: $src"; exit 1; }
    base="$(basename "$src")"
    # Notion's File Upload API rejects code/config extensions. Rename to .txt as a workaround.
    case ".${base##*.}" in
      .py|.sh|.bash|.md|.js|.ts|.jsx|.tsx|.yaml|.yml|.toml|.html|.css|.sql|.java|.cpp|.c|.h|.rb|.go|.rs|.swift|.xml|.ini|.cfg|.conf|.env)
        ntn files create --filename "${base}.txt" --content-type text/plain < "$src"
        ;;
      *)
        ntn files create --filename "$base" < "$src"
        ;;
    esac
    ;;

  list)
    [[ -f "$MAP" ]] || { echo "no tracked pages in $MAP"; exit 0; }
    column -t -s $'\t' < "$MAP"
    ;;

  *)
    sed -n '/^# Usage:/,/^$/p' "$0"; exit 1
    ;;
esac
