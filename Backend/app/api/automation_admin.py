"""Phase 10: workflow automation, scheduler, administration, integrations."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.db.session import SessionLocal
from app.models import User
from app.models.enums import DeliveryChannel, NotificationCategory, SecuritySeverity, WorkflowEntityType, WorkflowStatus
from app.services.automation_service import AutomationService

router = APIRouter(prefix="/admin", tags=["Phase10 Automation"])


def _ok(message: str, data: Any) -> dict[str, Any]:
    return {"success": True, "message": message, "data": data}


class WorkflowStepIn(BaseModel):
    step_name: str
    step_type: str = "APPROVAL"
    approver_role: str | None = None
    approver_user_id: int | None = None
    sla_minutes: int = 1440
    conditions: dict[str, Any] | None = None


class WorkflowUpsertIn(BaseModel):
    restaurant_id: UUID
    name: str
    code: str
    entity_type: WorkflowEntityType
    description: str | None = None
    trigger_event: str | None = None
    steps: list[WorkflowStepIn] = Field(default_factory=list)


class WorkflowInstanceIn(BaseModel):
    workflow_definition_id: UUID
    entity_id: str
    payload: dict[str, Any] | None = None


class WorkflowDecisionIn(BaseModel):
    decision: WorkflowStatus
    remarks: str | None = None


class DispatchNotificationIn(BaseModel):
    title: str
    body: str
    restaurant_id: UUID | None = None
    category: NotificationCategory = NotificationCategory.INFORMATION
    channels: list[DeliveryChannel] = Field(default_factory=lambda: [DeliveryChannel.IN_APP])
    recipient_user_id: int | None = None


class JobUpsertIn(BaseModel):
    restaurant_id: UUID
    name: str
    code: str
    schedule_cron: str | None = None
    timezone: str = "Asia/Kolkata"
    max_retries: int = 3
    config: dict[str, Any] | None = None


class JobPauseIn(BaseModel):
    paused: bool


class ReportScheduleIn(BaseModel):
    id: UUID | None = None
    restaurant_id: UUID
    report_kind: str
    frequency: str
    delivery_channel: DeliveryChannel = DeliveryChannel.EMAIL
    export_format: str = "PDF"
    recipients: dict[str, Any] | None = None
    filters: dict[str, Any] | None = None


class SettingUpsertIn(BaseModel):
    scope_type: str
    scope_id: str | None = None
    setting_key: str
    setting_value: dict[str, Any]
    is_secret: bool = False


class FileAssetIn(BaseModel):
    restaurant_id: UUID | None = None
    branch_id: UUID | None = None
    category: str
    file_name: str
    storage_path: str
    mime_type: str | None = None
    file_size_bytes: int = 0
    checksum: str | None = None
    metadata_json: dict[str, Any] | None = None


class ApiKeyIn(BaseModel):
    restaurant_id: UUID | None = None
    name: str
    scopes: dict[str, Any] | None = None
    requests_per_minute: int = 120


class WebhookIn(BaseModel):
    restaurant_id: UUID | None = None
    name: str
    url: str
    subscribed_events: list[str] = Field(default_factory=list)


class IntegrationIn(BaseModel):
    restaurant_id: UUID
    provider: str
    status: str = "CONNECTED"
    config: dict[str, Any] | None = None


class SecurityAlertIn(BaseModel):
    restaurant_id: UUID | None = None
    user_id: int | None = None
    severity: SecuritySeverity = SecuritySeverity.WARNING
    alert_type: str
    title: str
    body: str
    payload: dict[str, Any] | None = None


@router.get("/workflows")
def list_workflows(
    restaurant_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return _ok("Workflows fetched", AutomationService(db).list_workflows(restaurant_id))


@router.post("/workflows")
def upsert_workflow(
    payload: WorkflowUpsertIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    data = AutomationService(db).upsert_workflow(
        restaurant_id=payload.restaurant_id,
        name=payload.name,
        code=payload.code,
        entity_type=payload.entity_type,
        steps=[s.model_dump() for s in payload.steps],
        description=payload.description,
        trigger_event=payload.trigger_event,
        actor_user_id=user.id,
    )
    return _ok("Workflow saved", data)


@router.post("/workflows/instances")
def start_workflow(
    payload: WorkflowInstanceIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    data = AutomationService(db).start_workflow_instance(
        workflow_definition_id=payload.workflow_definition_id,
        entity_id=payload.entity_id,
        requested_by_user_id=user.id,
        payload=payload.payload,
    )
    return _ok("Workflow started", data)


@router.post("/workflows/instances/{instance_id}/decision")
def decide_workflow(
    instance_id: UUID,
    payload: WorkflowDecisionIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    data = AutomationService(db).decide_workflow_step(
        instance_id=instance_id,
        decision=payload.decision,
        remarks=payload.remarks,
        actor_user_id=user.id,
    )
    return _ok("Workflow decision saved", data)


@router.post("/notifications/dispatch")
def dispatch_notification(
    payload: DispatchNotificationIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    data = AutomationService(db).dispatch_notification(
        title=payload.title,
        body=payload.body,
        restaurant_id=payload.restaurant_id,
        category=payload.category,
        channels=payload.channels,
        recipient_user_id=payload.recipient_user_id,
        actor_user_id=user.id,
    )
    return _ok("Notification dispatched", data)


@router.get("/notifications/deliveries")
def list_deliveries(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return _ok("Notification deliveries fetched", AutomationService(db).list_delivery_log(limit=limit))


@router.get("/jobs")
def list_jobs(
    restaurant_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return _ok("Job definitions fetched", AutomationService(db).list_jobs(restaurant_id))


@router.post("/jobs")
def upsert_job(
    payload: JobUpsertIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    data = AutomationService(db).upsert_job(
        restaurant_id=payload.restaurant_id,
        name=payload.name,
        code=payload.code,
        schedule_cron=payload.schedule_cron,
        timezone_name=payload.timezone,
        max_retries=payload.max_retries,
        config=payload.config,
        actor_user_id=user.id,
    )
    return _ok("Job saved", data)


@router.post("/jobs/bootstrap")
def bootstrap_jobs(
    restaurant_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    created = AutomationService(db).bootstrap_default_jobs(restaurant_id, actor_user_id=user.id)
    return _ok("Default jobs ensured", {"created": created})


@router.post("/jobs/{job_id}/pause")
def pause_job(
    job_id: UUID,
    payload: JobPauseIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    data = AutomationService(db).set_job_paused(job_id, paused=payload.paused, actor_user_id=user.id)
    return _ok("Job pause state updated", data)


@router.post("/jobs/{job_id}/run-now")
def run_job_now(
    job_id: UUID,
    bg: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    data = AutomationService(db).enqueue_job_run(job_id=job_id, trigger_type="MANUAL", actor_user_id=user.id)
    run_id = UUID(data["run_id"])

    def _execute(run_uuid: UUID) -> None:
        bg_db = SessionLocal()
        try:
            AutomationService(bg_db).execute_job_run(run_uuid)
        finally:
            bg_db.close()

    bg.add_task(_execute, run_id)
    return _ok("Job enqueued", data)


@router.get("/jobs/runs")
def list_job_runs(
    job_id: UUID | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return _ok("Job runs fetched", AutomationService(db).list_job_runs(job_id=job_id, limit=limit))


@router.post("/report-schedules")
def upsert_report_schedule(
    payload: ReportScheduleIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    data = AutomationService(db).upsert_report_schedule(
        schedule_id=payload.id,
        restaurant_id=payload.restaurant_id,
        created_by_user_id=user.id,
        report_kind=payload.report_kind,
        frequency=payload.frequency,
        delivery_channel=payload.delivery_channel,
        export_format=payload.export_format,
        recipients=payload.recipients,
        filters=payload.filters,
    )
    return _ok("Report schedule saved", data)


@router.get("/report-schedules")
def list_report_schedules(
    restaurant_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return _ok("Report schedules fetched", AutomationService(db).list_report_schedules(restaurant_id))


@router.post("/settings")
def upsert_setting(
    payload: SettingUpsertIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    data = AutomationService(db).set_setting(
        scope_type=payload.scope_type,
        scope_id=payload.scope_id,
        setting_key=payload.setting_key,
        setting_value=payload.setting_value,
        actor_user_id=user.id,
        is_secret=payload.is_secret,
    )
    return _ok("Setting saved", data)


@router.get("/settings")
def list_settings(
    scope_type: str | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return _ok("Settings fetched", AutomationService(db).list_settings(scope_type=scope_type))


@router.post("/files/assets")
def register_file_asset(
    payload: FileAssetIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    data = AutomationService(db).register_file_asset(
        restaurant_id=payload.restaurant_id,
        branch_id=payload.branch_id,
        uploaded_by_user_id=user.id,
        category=payload.category,
        file_name=payload.file_name,
        storage_path=payload.storage_path,
        mime_type=payload.mime_type,
        file_size_bytes=payload.file_size_bytes,
        checksum=payload.checksum,
        metadata_json=payload.metadata_json,
    )
    return _ok("File metadata stored", data)


@router.get("/files/assets")
def list_file_assets(
    restaurant_id: UUID | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return _ok("File assets fetched", AutomationService(db).list_file_assets(restaurant_id=restaurant_id, limit=limit))


@router.post("/api-keys")
def create_api_key(
    payload: ApiKeyIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    data = AutomationService(db).create_api_key(
        restaurant_id=payload.restaurant_id,
        name=payload.name,
        scopes=payload.scopes,
        requests_per_minute=payload.requests_per_minute,
        actor_user_id=user.id,
    )
    return _ok("API key created", data)


@router.get("/api-keys")
def list_api_keys(
    restaurant_id: UUID | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return _ok("API keys fetched", AutomationService(db).list_api_keys(restaurant_id))


@router.post("/webhooks")
def create_webhook(
    payload: WebhookIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    data = AutomationService(db).create_webhook(
        restaurant_id=payload.restaurant_id,
        name=payload.name,
        url=payload.url,
        subscribed_events=payload.subscribed_events,
        actor_user_id=user.id,
    )
    return _ok("Webhook created", data)


@router.get("/webhooks")
def list_webhooks(
    restaurant_id: UUID | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return _ok("Webhooks fetched", AutomationService(db).list_webhooks(restaurant_id))


@router.post("/integrations")
def upsert_integration(
    payload: IntegrationIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    data = AutomationService(db).upsert_integration(
        restaurant_id=payload.restaurant_id,
        provider=payload.provider,
        status=payload.status,
        config=payload.config,
        actor_user_id=user.id,
    )
    return _ok("Integration updated", data)


@router.get("/integrations")
def list_integrations(
    restaurant_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return _ok("Integrations fetched", AutomationService(db).list_integrations(restaurant_id))


@router.get("/audit/logs")
def list_audit_logs(
    limit: int = Query(default=300, ge=1, le=2000),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return _ok("Audit logs fetched", AutomationService(db).list_audit_logs(limit=limit))


@router.post("/security/alerts")
def create_security_alert(
    payload: SecurityAlertIn,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict[str, Any]:
    data = AutomationService(db).create_security_alert(
        restaurant_id=payload.restaurant_id,
        user_id=payload.user_id,
        severity=payload.severity,
        alert_type=payload.alert_type,
        title=payload.title,
        body=payload.body,
        payload=payload.payload,
    )
    return _ok("Security alert created", data)


@router.get("/security/overview")
def security_overview(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return _ok("Security overview fetched", AutomationService(db).security_overview())


@router.get("/system-health")
def system_health(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return _ok("System health fetched", AutomationService(db).system_health())


@router.get("/dashboard")
def admin_dashboard(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return _ok("Admin dashboard fetched", AutomationService(db).admin_dashboard())

