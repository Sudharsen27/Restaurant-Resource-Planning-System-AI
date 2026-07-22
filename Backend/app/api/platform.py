"""Phase 12 platform / ops admin APIs — cache, queue, logs, migrations, backups."""

from __future__ import annotations

from collections import deque
from threading import Lock
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.api.dependencies import require_roles
from app.core.config import settings
from app.services.cache_service import get_cache_service
from app.services.deployment_utils import (
    alembic_current,
    alembic_heads,
    create_postgres_backup,
    disk_for_backups,
    list_backups,
    prune_backups,
)
from app.services.health_service import get_health_service
from app.services.queue_service import get_queue_service
from app.services.storage_service import get_storage_service

router = APIRouter(prefix="/platform", tags=["platform"])

# In-process ring buffer of recent log-ish events for the Log Viewer UI
_LOG_BUFFER: deque[dict[str, Any]] = deque(maxlen=500)
_LOG_LOCK = Lock()


def push_platform_log(event: str, message: str, level: str = "INFO", **extra: Any) -> None:
    from datetime import datetime, timezone

    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "event": event,
        "message": message,
        **extra,
    }
    with _LOG_LOCK:
        _LOG_BUFFER.appendleft(entry)


class EnqueueRequest(BaseModel):
    job_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    countdown: int | None = None


class CacheClearRequest(BaseModel):
    namespace: str = "cache"


class CacheSetRequest(BaseModel):
    key: str
    value: Any
    ttl: int | None = 300
    namespace: str = "cache"


@router.get("/health-center")
def health_center(_user=Depends(require_roles("SUPER_ADMIN", "ADMIN", "MANAGER"))):
    push_platform_log("health_center", "Health center viewed")
    return {"success": True, "data": get_health_service().detailed()}


@router.get("/deployment")
def deployment_status(_user=Depends(require_roles("SUPER_ADMIN", "ADMIN"))):
    return {
        "success": True,
        "data": {
            "deployment_id": settings.deployment_id,
            "region": settings.deployment_region,
            "git_sha": settings.git_sha,
            "build_timestamp": settings.build_timestamp,
            "app_env": settings.app_env,
            "app_version": settings.app_version,
            "storage_backend": settings.storage_backend,
            "redis_enabled": settings.redis_enabled,
            "rate_limit_enabled": settings.rate_limit_enabled,
            "csrf_enabled": settings.csrf_enabled,
            "https_redirect_enabled": settings.https_redirect_enabled,
            "alembic": alembic_current(),
            "alembic_heads": alembic_heads(),
        },
    }


@router.get("/migrations")
def migration_dashboard(_user=Depends(require_roles("SUPER_ADMIN", "ADMIN"))):
    return {
        "success": True,
        "data": {
            "current": alembic_current(),
            "heads": alembic_heads(),
            "use_alembic": settings.use_alembic,
            "allow_create_all": settings.allow_create_all,
        },
    }


@router.get("/cache")
def cache_status(_user=Depends(require_roles("SUPER_ADMIN", "ADMIN"))):
    cache = get_cache_service()
    return {
        "success": True,
        "data": {
            "backend": cache.backend,
            "ping": cache.ping(),
            "key_prefix": settings.redis_key_prefix,
            "default_ttl": settings.redis_cache_default_ttl_seconds,
        },
    }


@router.post("/cache/clear")
def cache_clear(body: CacheClearRequest, _user=Depends(require_roles("SUPER_ADMIN", "ADMIN"))):
    deleted = get_cache_service().clear_namespace(body.namespace)
    push_platform_log("cache_clear", f"Cleared namespace {body.namespace}", deleted=deleted)
    return {"success": True, "data": {"deleted": deleted, "namespace": body.namespace}}


@router.post("/cache/set")
def cache_set(body: CacheSetRequest, _user=Depends(require_roles("SUPER_ADMIN", "ADMIN"))):
    get_cache_service().set(body.namespace, body.key, body.value, ttl=body.ttl)
    return {"success": True, "data": {"key": body.key, "namespace": body.namespace}}


@router.get("/cache/get")
def cache_get(
    key: str = Query(...),
    namespace: str = Query("cache"),
    _user=Depends(require_roles("SUPER_ADMIN", "ADMIN")),
):
    value = get_cache_service().get(namespace, key)
    return {"success": True, "data": {"key": key, "namespace": namespace, "value": value}}


@router.get("/queue")
def queue_monitor(_user=Depends(require_roles("SUPER_ADMIN", "ADMIN", "MANAGER"))):
    qs = get_queue_service()
    return {
        "success": True,
        "data": {
            "health": qs.health(),
            "depth": qs.purge_stats(),
            "job_types": list(qs.TASK_MAP.keys()),
        },
    }


@router.post("/queue/enqueue")
def queue_enqueue(body: EnqueueRequest, _user=Depends(require_roles("SUPER_ADMIN", "ADMIN"))):
    result = get_queue_service().enqueue(body.job_type, body.payload, countdown=body.countdown)
    push_platform_log("queue_enqueue", f"Enqueued {body.job_type}", **result)
    return {"success": True, "data": result}


@router.get("/queue/tasks/{task_id}")
def queue_task_status(task_id: str, _user=Depends(require_roles("SUPER_ADMIN", "ADMIN", "MANAGER"))):
    return {"success": True, "data": get_queue_service().status(task_id)}


@router.get("/logs")
def log_viewer(
    limit: int = Query(100, ge=1, le=500),
    _user=Depends(require_roles("SUPER_ADMIN", "ADMIN")),
):
    with _LOG_LOCK:
        entries = list(_LOG_BUFFER)[:limit]
    return {"success": True, "data": {"entries": entries, "count": len(entries)}}


@router.get("/monitoring")
def system_monitoring(_user=Depends(require_roles("SUPER_ADMIN", "ADMIN", "MANAGER"))):
    detailed = get_health_service().detailed()
    return {
        "success": True,
        "data": {
            **detailed,
            "backups": disk_for_backups(),
            "storage": get_storage_service().health(),
        },
    }


@router.get("/backups")
def backups_list(_user=Depends(require_roles("SUPER_ADMIN", "ADMIN"))):
    return {"success": True, "data": {"items": list_backups(), "disk": disk_for_backups()}}


@router.post("/backups/run")
def backups_run(_user=Depends(require_roles("SUPER_ADMIN"))):
    result = create_postgres_backup(label="manual")
    push_platform_log("backup_run", "Manual backup", level="INFO", **{k: v for k, v in result.items() if k != "path"})
    return {"success": bool(result.get("ok")), "data": result}


@router.post("/backups/prune")
def backups_prune(_user=Depends(require_roles("SUPER_ADMIN"))):
    result = prune_backups()
    return {"success": True, "data": result}


@router.get("/storage")
def storage_status(_user=Depends(require_roles("SUPER_ADMIN", "ADMIN"))):
    return {
        "success": True,
        "data": {
            "backend": settings.storage_backend,
            "health": get_storage_service().health(),
            "public_base_url": settings.storage_public_base_url,
        },
    }