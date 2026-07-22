#!/usr/bin/env bash
# Verify backup file integrity (exists, size, gzip, sha256).
set -euo pipefail

FILE="${1:-}"
if [[ -z "$FILE" || ! -f "$FILE" ]]; then
  echo "Usage: $0 <backup-file>"
  exit 1
fi

BYTES=$(wc -c < "$FILE" | tr -d ' ')
if [[ "$BYTES" -lt 50 ]]; then
  echo "FAIL: backup too small ($BYTES bytes)"
  exit 1
fi

if [[ "$FILE" == *.gz ]]; then
  gzip -t "$FILE"
  echo "OK: gzip integrity"
fi

sha256sum "$FILE" || shasum -a 256 "$FILE"
echo "OK: backup verified ($BYTES bytes)"
