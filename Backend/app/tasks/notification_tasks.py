"""Notification dispatch jobs."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from celery import shared_task

from app.core.config import settings

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="app.tasks.notification_tasks.dispatch_notification_job",
    max_retries=settings.celery_task_max_retries,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def dispatch_notification_job(
    self,
    *,
    channel: str = "in_app",
    recipient: str | None = None,
    title: str = "",
    body: str = "",
    meta: dict | None = None,
) -> dict:
    logger.info(
        "Notification job",
        extra={
            "event": "notification_job",
            "channel": channel,
            "recipient": recipient,
            "title": title,
        },
    )
    return {
        "ok": True,
        "channel": channel,
        "recipient": recipient,
        "title": title,
        "dispatched_at": datetime.now(timezone.utc).isoformat(),
        "meta": meta or {},
    }
