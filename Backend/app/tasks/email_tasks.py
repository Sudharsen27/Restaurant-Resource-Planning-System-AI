"""Email background jobs."""

from __future__ import annotations

import logging

from celery import shared_task

from app.core.config import settings

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="app.tasks.email_tasks.send_email_job",
    max_retries=settings.celery_task_max_retries,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
)
def send_email_job(self, *, to: str, subject: str, body: str, template: str | None = None) -> dict:
    """Placeholder email sender — integrate SMTP/SES/SendGrid in production."""
    logger.info(
        "Email job",
        extra={
            "event": "email_job",
            "to": to,
            "subject": subject,
            "template": template,
            "retries": self.request.retries,
        },
    )
    # Intentionally no real SMTP in Phase 12 scaffold — logs + succeeds for queue verification
    return {"sent": True, "to": to, "subject": subject, "provider": "log"}
