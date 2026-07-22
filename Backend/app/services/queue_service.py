"""Queue facade — enqueue Celery jobs with optional eager/local fallback."""

from __future__ import annotations

import logging
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)


class QueueService:
    """Thin wrapper around Celery for typed enqueue + health."""

    TASK_MAP = {
        "email": "app.tasks.email_tasks.send_email_job",
        "report": "app.tasks.report_tasks.generate_scheduled_report",
        "inventory_check": "app.tasks.inventory_tasks.check_low_stock",
        "notification": "app.tasks.notification_tasks.dispatch_notification_job",
        "analytics": "app.tasks.analytics_tasks.process_analytics_job",
    }

    def enqueue(
        self,
        job_type: str,
        payload: dict[str, Any] | None = None,
        *,
        countdown: int | None = None,
        queue: str | None = None,
    ) -> dict[str, Any]:
        payload = payload or {}
        task_name = self.TASK_MAP.get(job_type)
        if not task_name:
            raise ValueError(f"Unknown job_type: {job_type}")

        try:
            from app.celery_app import celery

            options: dict[str, Any] = {}
            if countdown is not None:
                options["countdown"] = countdown
            if queue:
                options["queue"] = queue
            async_result = celery.send_task(task_name, kwargs=payload, **options)
            return {
                "job_type": job_type,
                "task_id": async_result.id,
                "status": "queued",
                "eager": bool(settings.celery_task_always_eager),
            }
        except Exception as exc:
            logger.exception("Failed to enqueue job", extra={"event": "queue_enqueue_error"})
            return {
                "job_type": job_type,
                "task_id": None,
                "status": "error",
                "error": str(exc),
            }

    def status(self, task_id: str) -> dict[str, Any]:
        try:
            from app.celery_app import celery

            result = celery.AsyncResult(task_id)
            return {
                "task_id": task_id,
                "state": result.state,
                "ready": result.ready(),
                "successful": result.successful() if result.ready() else None,
                "result": result.result if result.ready() and result.successful() else None,
            }
        except Exception as exc:
            return {"task_id": task_id, "state": "UNKNOWN", "error": str(exc)}

    def health(self) -> dict[str, Any]:
        try:
            from app.celery_app import celery

            inspector = celery.control.inspect(timeout=1.0)
            ping = inspector.ping() if inspector else None
            stats = inspector.stats() if inspector and ping else None
            active = inspector.active() if inspector and ping else None
            workers = list(ping.keys()) if ping else []
            active_count = sum(len(v or []) for v in (active or {}).values())
            return {
                "ok": bool(workers),
                "workers": workers,
                "active_tasks": active_count,
                "broker": settings.celery_broker_url.split("@")[-1],
                "stats_available": bool(stats),
            }
        except Exception as exc:
            return {
                "ok": False,
                "workers": [],
                "error": str(exc),
                "broker": settings.celery_broker_url.split("@")[-1],
            }

    def purge_stats(self) -> dict[str, Any]:
        """Return lightweight queue depth via Redis when possible."""
        try:
            from app.services.cache_service import get_cache_service

            cache = get_cache_service()
            if cache.backend != "redis" or cache._redis is None:
                return {"depth_known": False}
            # Default Celery queue name
            depth = int(cache._redis.llen("celery") or 0)
            return {"depth_known": True, "default_queue_depth": depth}
        except Exception as exc:
            return {"depth_known": False, "error": str(exc)}


_queue_service: QueueService | None = None


def get_queue_service() -> QueueService:
    global _queue_service
    if _queue_service is None:
        _queue_service = QueueService()
    return _queue_service
