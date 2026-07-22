#!/usr/bin/env bash
# Automated PostgreSQL backup with retention pruning.
# Usage: ./scripts/backup_postgres.sh [label]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

: "${DATABASE_URL:=postgresql://postgres:postgres@localhost:5432/restaurant_rps}"
: "${BACKUP_DIR:=${ROOT}/backups}"
: "${BACKUP_RETENTION_DAYS:=14}"
export LABEL="${1:-auto}"
export DATABASE_URL BACKUP_DIR BACKUP_RETENTION_DAYS

python - <<'PY'
from app.services.deployment_utils import create_postgres_backup, prune_backups
import json, os
result = create_postgres_backup(label=os.environ.get("LABEL", "auto"))
print(json.dumps(result, indent=2))
if not result.get("ok"):
    raise SystemExit(1)
print(json.dumps(prune_backups(), indent=2))
PY
