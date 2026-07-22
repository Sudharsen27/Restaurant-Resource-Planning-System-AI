#!/usr/bin/env python
"""Safe schema migrate entrypoint for Docker / CI.

Handles fresh empty Postgres volumes where the historical Alembic root
migration expects a pre-existing ``users`` table.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure Backend package root is importable when invoked as scripts/migrate.py
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def main() -> int:
    from app.core.config import settings
    from app.core.logging import setup_logging
    from app.database.init_db import init_database

    setup_logging(level=settings.log_level, log_format=settings.log_format)
    try:
        init_database()
    except Exception as exc:
        print(f"Migration failed: {exc}", file=sys.stderr)
        raise
    print("Schema migrate OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
