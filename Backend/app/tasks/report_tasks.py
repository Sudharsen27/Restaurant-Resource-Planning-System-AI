"""Scheduled report jobs."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from celery import shared_task

from app.core.config import settings

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="app.tasks.report_tasks.generate_scheduled_report",
    max_retries=settings.celery_task_max_retries,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def generate_scheduled_report(self, *, schedule_id: int | None = None, report_type: str = "sales") -> dict:
    logger.info(
        "Generate scheduled report",
        extra={"event": "report_job", "schedule_id": schedule_id, "report_type": report_type},
    )
    return {
        "ok": True,
        "schedule_id": schedule_id,
        "report_type": report_type,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@shared_task(name="app.tasks.report_tasks.dispatch_due_reports")
def dispatch_due_reports() -> dict:
    """Beat entrypoint — scan due schedules and enqueue report jobs."""
    logger.info("Dispatch due reports tick", extra={"event": "report_dispatch"})
    # Hook point for AutomationService report schedules
    return {"dispatched": 0, "at": datetime.now(timezone.utc).isoformat()}
