#!/usr/bin/env bash
# PostToolUse hook — tự động format file vừa Write/Edit.
#   backend/*.py                → ruff format + ruff check --fix   (từ backend/)
#   frontend/*.{ts,tsx,js,jsx,mjs,cjs,json,css}
#                               → prettier --write (+ eslint --fix cho js/ts)  (từ frontend/)
# No-op với file/loại khác. Mọi bước || true → hook lỗi không chặn công việc.

set -uo pipefail

input="$(cat)"
fp="$(printf '%s' "$input" | python3 -c \
  "import json,sys; print((json.load(sys.stdin).get('tool_input') or {}).get('file_path','') or '')" \
  2>/dev/null || true)"

[ -z "$fp" ] && exit 0

case "$fp" in
  # --- Backend Python ---
  *.py)
    case "$fp" in
      */backend/*)
        backend="${fp%%/backend/*}/backend"
        cd "$backend" || exit 0
        uv run ruff format "$fp" >/dev/null 2>&1 || true
        uv run ruff check --fix "$fp" >/dev/null 2>&1 || true
        ;;
    esac
    ;;

  # --- Frontend ---
  */frontend/*.ts | */frontend/*.tsx | */frontend/*.js | */frontend/*.jsx | \
  */frontend/*.mjs | */frontend/*.cjs | */frontend/*.json | */frontend/*.css)
    frontend="${fp%%/frontend/*}/frontend"
    cd "$frontend" || exit 0
    npx --no-install prettier --write "$fp" >/dev/null 2>&1 || true
    case "$fp" in
      *.ts | *.tsx | *.js | *.jsx)
        npx --no-install eslint --fix "$fp" >/dev/null 2>&1 || true
        ;;
    esac
    ;;
esac

exit 0
