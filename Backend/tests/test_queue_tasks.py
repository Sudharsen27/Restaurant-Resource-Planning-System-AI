"""Queue service and Celery task smoke tests (eager mode)."""

from app.services.queue_service import QueueService
from app.tasks.email_tasks import send_email_job
from app.tasks.notification_tasks import dispatch_notification_job


def test_task_map_covers_required_jobs():
    qs = QueueService()
    for key in ("email", "report", "inventory_check", "notification", "analytics"):
        assert key in qs.TASK_MAP


def test_email_job_eager():
    result = send_email_job.apply(
        kwargs={"to": "a@b.com", "subject": "Hi", "body": "Body"}
    ).get()
    assert result["sent"] is True
    assert result["to"] == "a@b.com"


def test_notification_job_eager():
    result = dispatch_notification_job.apply(
        kwargs={"channel": "in_app", "title": "T", "body": "B"}
    ).get()
    assert result["ok"] is True
