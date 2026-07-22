"""Analytics processing jobs."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from celery import shared_task

from app.core.config import settings

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="app.tasks.analytics_tasks.process_analytics_job",
    max_retries=settings.celery_task_max_retries,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def process_analytics_job(self, *, restaurant_id: int | None = None, job: str = "rollup") -> dict:
    logger.info(
        "Analytics job",
        extra={"event": "analytics_job", "restaurant_id": restaurant_id, "job": job},
    )
    return {
        "ok": True,
        "job": job,
        "restaurant_id": restaurant_id,
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }


@shared_task(name="app.tasks.analytics_tasks.process_nightly_analytics")
def process_nightly_analytics() -> dict:
    logger.info("Nightly analytics tick", extra={"event": "analytics_nightly"})
    return process_analytics_job.apply(kwargs={"job": "nightly_rollup"}).get()
