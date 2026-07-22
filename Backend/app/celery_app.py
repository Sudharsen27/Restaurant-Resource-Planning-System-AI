"""Celery application factory for background jobs."""

from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings


def create_celery() -> Celery:
    app = Celery(
        "restaurant_erp",
        broker=settings.celery_broker_url,
        backend=settings.celery_result_backend,
        include=[
            "app.tasks.email_tasks",
            "app.tasks.report_tasks",
            "app.tasks.inventory_tasks",
            "app.tasks.notification_tasks",
            "app.tasks.analytics_tasks",
        ],
    )
    app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_acks_late=settings.celery_task_acks_late,
        task_default_retry_delay=settings.celery_task_default_retry_delay,
        task_always_eager=settings.celery_task_always_eager or settings.is_testing,
        worker_prefetch_multiplier=1,
        task_track_started=True,
        result_expires=86400,
        beat_schedule={
            "inventory-low-stock-hourly": {
                "task": "app.tasks.inventory_tasks.check_low_stock",
                "schedule": crontab(minute=0),
            },
            "analytics-nightly": {
                "task": "app.tasks.analytics_tasks.process_nightly_analytics",
                "schedule": crontab(hour=2, minute=15),
            },
            "scheduled-reports-hourly": {
                "task": "app.tasks.report_tasks.dispatch_due_reports",
                "schedule": crontab(minute=5),
            },
        },
    )
    return app


celery = create_celery()
