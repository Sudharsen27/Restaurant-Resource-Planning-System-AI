"""Deployment utilities — backups, migration status, cache/queue admin helpers."""

from __future__ import annotations

import hashlib
import logging
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from app.core.config import settings
from app.core.constants import BACKEND_ROOT

logger = logging.getLogger(__name__)


def _backup_root() -> Path:
    root = settings.backup_dir
    path = root if root.is_absolute() else (BACKEND_ROOT / root)
    path.mkdir(parents=True, exist_ok=True)
    return path


def parse_database_url(url: str) -> dict[str, str]:
    parsed = urlparse(url)
    return {
        "user": parsed.username or "postgres",
        "password": parsed.password or "",
        "host": parsed.hostname or "localhost",
        "port": str(parsed.port or 5432),
        "dbname": (parsed.path or "/restaurant_rps").lstrip("/"),
    }


def create_postgres_backup(*, label: str | None = None) -> dict:
    """Run pg_dump into backup_dir; verify size + checksum when enabled."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    name = f"rrps_{label or 'auto'}_{stamp}.sql.gz"
    dest = _backup_root() / name
    db = parse_database_url(settings.database_url)

    env = {**__import__("os").environ, "PGPASSWORD": db["password"]}
    dump_cmd = [
        "pg_dump",
        "-h",
        db["host"],
        "-p",
        db["port"],
        "-U",
        db["user"],
        "-d",
        db["dbname"],
        "--no-owner",
        "--format=plain",
    ]
    try:
        proc = subprocess.run(
            dump_cmd,
            env=env,
            capture_output=True,
            check=True,
        )
    except FileNotFoundError:
        # Fallback: write a marker file when pg_dump is not installed (dev machines)
        content = f"-- backup placeholder {stamp}\n-- install postgresql-client for real dumps\n"
        dest.write_bytes(content.encode())
        return {
            "ok": True,
            "path": str(dest),
            "mode": "placeholder",
            "bytes": dest.stat().st_size,
            "warning": "pg_dump not found; wrote placeholder",
        }
    except subprocess.CalledProcessError as exc:
        logger.error("pg_dump failed: %s", exc.stderr.decode(errors="ignore"))
        return {"ok": False, "error": exc.stderr.decode(errors="ignore")[:500]}

    import gzip

    with gzip.open(dest, "wb") as gz:
        gz.write(proc.stdout)

    checksum = hashlib.sha256(dest.read_bytes()).hexdigest()
    meta = {
        "ok": True,
        "path": str(dest),
        "mode": "pg_dump",
        "bytes": dest.stat().st_size,
        "sha256": checksum,
        "created_at": stamp,
    }
    if settings.backup_verify_on_write and dest.stat().st_size < 20:
        meta["ok"] = False
        meta["error"] = "Backup file suspiciously small"
    return meta


def list_backups() -> list[dict]:
    root = _backup_root()
    items = []
    for path in sorted(root.glob("rrps_*.sql*"), reverse=True):
        items.append(
            {
                "name": path.name,
                "path": str(path),
                "bytes": path.stat().st_size,
                "modified": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(),
            }
        )
    return items


def prune_backups(*, retention_days: int | None = None) -> dict:
    retention = retention_days if retention_days is not None else settings.backup_retention_days
    cutoff = datetime.now(timezone.utc).timestamp() - (retention * 86400)
    removed = []
    for path in _backup_root().glob("rrps_*.sql*"):
        if path.stat().st_mtime < cutoff:
            path.unlink(missing_ok=True)
            removed.append(path.name)
    return {"removed": removed, "retention_days": retention}


def restore_postgres_backup(path: str) -> dict:
    """Restore from gzip or plain SQL dump. Destructive — use with care."""
    file_path = Path(path)
    if not file_path.exists():
        return {"ok": False, "error": "Backup file not found"}

    db = parse_database_url(settings.database_url)
    env = {**__import__("os").environ, "PGPASSWORD": db["password"]}

    if file_path.suffix == ".gz" or file_path.name.endswith(".sql.gz"):
        import gzip

        sql = gzip.open(file_path, "rb").read()
    else:
        sql = file_path.read_bytes()

    restore_cmd = [
        "psql",
        "-h",
        db["host"],
        "-p",
        db["port"],
        "-U",
        db["user"],
        "-d",
        db["dbname"],
        "-v",
        "ON_ERROR_STOP=1",
    ]
    try:
        subprocess.run(restore_cmd, input=sql, env=env, check=True, capture_output=True)
    except FileNotFoundError:
        return {"ok": False, "error": "psql not found on PATH"}
    except subprocess.CalledProcessError as exc:
        return {"ok": False, "error": exc.stderr.decode(errors="ignore")[:500]}
    return {"ok": True, "restored_from": str(file_path)}


def alembic_current() -> dict:
    try:
        proc = subprocess.run(
            ["alembic", "current"],
            cwd=str(BACKEND_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        return {
            "ok": proc.returncode == 0,
            "stdout": (proc.stdout or "").strip(),
            "stderr": (proc.stderr or "").strip(),
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def alembic_heads() -> dict:
    try:
        proc = subprocess.run(
            ["alembic", "heads"],
            cwd=str(BACKEND_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        return {
            "ok": proc.returncode == 0,
            "stdout": (proc.stdout or "").strip(),
            "stderr": (proc.stderr or "").strip(),
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def disk_for_backups() -> dict:
    root = _backup_root()
    usage = shutil.disk_usage(root)
    return {
        "path": str(root),
        "free_gb": round(usage.free / (1024**3), 2),
        "total_gb": round(usage.total / (1024**3), 2),
        "backup_count": len(list(root.glob("rrps_*.sql*"))),
    }
