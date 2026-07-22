"""Platform health, readiness, and resource monitoring."""

from __future__ import annotations

import os
import platform
import shutil
import time
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings
from app.core.constants import APP_VERSION
from app.db.database import check_connection, engine


class HealthService:
    def liveness(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "check": "live",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def readiness(self) -> dict[str, Any]:
        checks = {
            "database": self._database(),
            "redis": self._redis(),
            "storage": self._storage(),
        }
        ok = all(c.get("ok") for c in checks.values())
        return {
            "status": "ok" if ok else "degraded",
            "check": "ready",
            "checks": checks,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def detailed(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "app": {
                "name": settings.app_name,
                "env": settings.app_env,
                "version": settings.app_version or APP_VERSION,
                "git_sha": settings.git_sha,
                "deployment_id": settings.deployment_id,
                "region": settings.deployment_region,
            },
            "database": self._database(),
            "redis": self._redis(),
            "queue": self._queue(),
            "storage": self._storage(),
            "resources": self._resources(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _database(self) -> dict[str, Any]:
        start = time.perf_counter()
        ok = check_connection()
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        pool = engine.pool
        info: dict[str, Any] = {
            "ok": ok,
            "latency_ms": latency_ms,
            "pool_size": getattr(pool, "size", lambda: None)(),
            "checked_in": getattr(pool, "checkedin", lambda: None)(),
            "checked_out": getattr(pool, "checkedout", lambda: None)(),
            "overflow": getattr(pool, "overflow", lambda: None)(),
        }
        return info

    def _redis(self) -> dict[str, Any]:
        from app.services.cache_service import get_cache_service

        cache = get_cache_service()
        start = time.perf_counter()
        ok = cache.ping()
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        return {
            "ok": ok,
            "backend": cache.backend,
            "latency_ms": latency_ms,
            "enabled": settings.redis_enabled,
        }

    def _queue(self) -> dict[str, Any]:
        from app.services.queue_service import get_queue_service

        qs = get_queue_service()
        health = qs.health()
        depth = qs.purge_stats()
        return {**health, **depth}

    def _storage(self) -> dict[str, Any]:
        from app.services.storage_service import get_storage_service

        try:
            return get_storage_service().health()
        except Exception as exc:
            return {"ok": False, "error": str(exc), "backend": settings.storage_backend}

    def _resources(self) -> dict[str, Any]:
        try:
            import psutil

            disk = shutil.disk_usage(os.getcwd())
            vm = psutil.virtual_memory()
            return {
                "ok": True,
                "cpu_percent": psutil.cpu_percent(interval=0.05),
                "memory": {
                    "percent": vm.percent,
                    "used_mb": round(vm.used / (1024 * 1024), 1),
                    "available_mb": round(vm.available / (1024 * 1024), 1),
                },
                "disk": {
                    "percent": round(disk.used / disk.total * 100, 1),
                    "used_gb": round(disk.used / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                },
                "platform": platform.platform(),
                "python": platform.python_version(),
            }
        except Exception as exc:
            return {"ok": False, "error": str(exc)}


_health_service: HealthService | None = None


def get_health_service() -> HealthService:
    global _health_service
    if _health_service is None:
        _health_service = HealthService()
    return _health_service
