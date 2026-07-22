#!/usr/bin/env bash
# Restore PostgreSQL from a backup created by backup_postgres.sh
# Usage: ./scripts/restore_postgres.sh /path/to/rrps_auto_....sql.gz
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

BACKUP_PATH="${1:-}"
if [[ -z "$BACKUP_PATH" ]]; then
  echo "Usage: $0 <backup.sql.gz>"
  exit 1
fi

: "${DATABASE_URL:=postgresql://postgres:postgres@localhost:5432/restaurant_rps}"

python - <<PY
from app.services.deployment_utils import restore_postgres_backup
import json, sys
result = restore_postgres_backup(r"""$BACKUP_PATH""")
print(json.dumps(result, indent=2))
sys.exit(0 if result.get("ok") else 1)
PY
