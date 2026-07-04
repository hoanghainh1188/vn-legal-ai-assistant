#!/usr/bin/env bash
# PostToolUse hook — tự động format + lint-fix file Python vừa Write/Edit.
# Chỉ tác động file *.py nằm trong backend/ (nơi có ruff + uv). No-op với file khác.
# Đọc JSON tool input từ stdin, lấy file_path, chạy ruff từ thư mục backend.

set -euo pipefail

input="$(cat)"
fp="$(printf '%s' "$input" | python3 -c \
  "import json,sys; print((json.load(sys.stdin).get('tool_input') or {}).get('file_path','') or '')" \
  2>/dev/null || true)"

# Chỉ xử lý file Python trong backend/
case "$fp" in
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
esac

exit 0
