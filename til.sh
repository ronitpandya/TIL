#!/usr/bin/env bash
# TIL helper: scaffold today's entry and regenerate the README index.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cmd_new() {
  local today year month_num month_name dir file
  today="$(date +%Y-%m-%d)"
  year="$(date +%Y)"
  month_num="$(date +%m)"
  month_name="$(date +%B)"
  dir="$ROOT/$year/${month_num}-${month_name}"
  file="$dir/${today}.md"

  mkdir -p "$dir"
  if [ -f "$file" ]; then
    echo "Today's entry already exists: ${file#$ROOT/}"
  else
    sed "s/{{DATE}}/$today/g" "$ROOT/templates/entry-template.md" > "$file"
    echo "Created ${file#$ROOT/}"
  fi

  if command -v code >/dev/null 2>&1; then
    code "$file"
  fi
}

cmd_index() {
  python3 "$ROOT/scripts/generate_index.py"
}

case "${1:-}" in
  new) cmd_new ;;
  index) cmd_index ;;
  *)
    echo "Usage: ./til.sh {new|index}"
    echo "  new    Scaffold (and open) today's entry"
    echo "  index  Regenerate README.md from all entries"
    exit 1
    ;;
esac
