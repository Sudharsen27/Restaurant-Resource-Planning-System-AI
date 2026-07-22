"""Phase 10 services: workflow automation, scheduler, admin, and health."""

from __future__ import annotations

import hashlib
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    ApiCredential,
    ApiRequestLog,
    FileAsset,
    IntegrationConnector,
    JobDefinition,
    JobRun,
    LoginEvent,
    Notification,
    NotificationDelivery,
    ReportSchedule,
    SecurityAlert,
    SystemSetting,
    User,
    UserSession,
    WebhookDelivery,
    WebhookEndpoint,
    WorkflowDefinition,
    WorkflowInstance,
    WorkflowInstanceStep,
    WorkflowStep,
)
from app.models.enums import (
    ApiKeyStatus,
    AuditAction,
    DeliveryChannel,
    JobRunStatus,
    NotificationCategory,
    NotificationType,
    SecuritySeverity,
    WorkflowEntityType,
    WorkflowStatus,
)
from app.services.audit_service import write_audit
from app.services.notification_service import NotificationService


def _enum(value: Any) -> str:
    return value.value if hasattr(value, "value") else str(value)


def _to_out(row: Any, fields: list[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for field in fields:
        value = getattr(row, field)
        if isinstance(value, UUID):
            out[field] = str(value)
        elif isinstance(value, datetime):
            out[field] = value.isoformat()
        elif hasattr(value, "value"):
            out[field] = value.value
        else:
            out[field] = value
    return out


class AutomationService:
    """Reusable automation service for APIs and background tasks."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.notifications = NotificationService(db)

    # ── Workflow Engine ──────────────────────────────────────────────────────

    def list_workflows(self, restaurant_id: UUID) -> list[dict[str, Any]]:
        rows = self.db.scalars(
            select(WorkflowDefinition)
            .where(
                WorkflowDefinition.restaurant_id == restaurant_id,
                WorkflowDefinition.is_deleted.is_(False),
            )
            .order_by(WorkflowDefinition.name.asc())
        ).all()
        return [
            _to_out(
                row,
                [
                    "id",
                    "name",
                    "code",
                    "entity_type",
                    "description",
                    "trigger_event",
                    "is_default",
                    "is_active",
                ],
            )
            for row in rows
        ]

    def upsert_workflow(
        self,
        *,
        restaurant_id: UUID,
        name: str,
        code: str,
        entity_type: WorkflowEntityType,
        steps: list[dict[str, Any]],
        actor_user_id: int | None,
        description: str | None = None,
        trigger_event: str | None = None,
    ) -> dict[str, Any]:
        row = self.db.scalar(
            select(WorkflowDefinition).where(
                WorkflowDefinition.restaurant_id == restaurant_id,
                WorkflowDefinition.code == code,
                WorkflowDefinition.is_deleted.is_(False),
            )
        )
        action = AuditAction.UPDATE if row else AuditAction.CREATE
        if not row:
            row = WorkflowDefinition(
                restaurant_id=restaurant_id,
                code=code,
                name=name,
                entity_type=entity_type,
            )
            self.db.add(row)
            self.db.flush()
        row.name = name
        row.entity_type = entity_type
        row.description = description
        row.trigger_event = trigger_event
        row.updated_by = actor_user_id

        existing = self.db.scalars(
            select(WorkflowStep).where(
                WorkflowStep.workflow_definition_id == row.id,
                WorkflowStep.is_deleted.is_(False),
            )
        ).all()
        for step in existing:
            step.soft_delete()

        for idx, step in enumerate(steps, start=1):
            self.db.add(
                WorkflowStep(
                    workflow_definition_id=row.id,
                    step_order=idx,
                    step_name=step.get("step_name") or f"Step {idx}",
                    step_type=step.get("step_type", "APPROVAL"),
                    approver_role=step.get("approver_role"),
                    approver_user_id=step.get("approver_user_id"),
                    sla_minutes=int(step.get("sla_minutes") or 1440),
                    conditions=step.get("conditions") or {},
                    created_by=actor_user_id,
                    updated_by=actor_user_id,
                )
            )

        write_audit(
            self.db,
            action=action,
            actor_user_id=actor_user_id,
            entity_type="workflow_definition",
            entity_id=str(row.id),
            details={"code": row.code, "entity_type": _enum(row.entity_type), "steps": len(steps)},
        )
        self.db.commit()
        return {"id": str(row.id), "code": row.code, "name": row.name, "steps_count": len(steps)}

    def start_workflow_instance(
        self,
        *,
        workflow_definition_id: UUID,
        entity_id: str,
        requested_by_user_id: int | None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        definition = self.db.get(WorkflowDefinition, workflow_definition_id)
        if not definition or definition.is_deleted:
            raise ValueError("Workflow definition not found")

        steps = self.db.scalars(
            select(WorkflowStep)
            .where(
                WorkflowStep.workflow_definition_id == definition.id,
                WorkflowStep.is_deleted.is_(False),
            )
            .order_by(WorkflowStep.step_order.asc())
        ).all()
        if not steps:
            raise ValueError("Workflow has no steps")

        inst = WorkflowInstance(
            workflow_definition_id=definition.id,
            entity_type=definition.entity_type,
            entity_id=entity_id,
            requested_by_user_id=requested_by_user_id,
            status=WorkflowStatus.PENDING,
            current_step_order=1,
            submitted_at=datetime.now(timezone.utc),
            payload=payload or {},
            created_by=requested_by_user_id,
            updated_by=requested_by_user_id,
        )
        self.db.add(inst)
        self.db.flush()

        for step in steps:
            self.db.add(
                WorkflowInstanceStep(
                    workflow_instance_id=inst.id,
                    step_order=step.step_order,
                    step_name=step.step_name,
                    approver_user_id=step.approver_user_id,
                    status=WorkflowStatus.PENDING,
                    created_by=requested_by_user_id,
                    updated_by=requested_by_user_id,
                )
            )

        self.db.commit()
        return {
            "instance_id": str(inst.id),
            "status": _enum(inst.status),
            "entity_type": _enum(inst.entity_type),
            "entity_id": entity_id,
        }

    def decide_workflow_step(
        self,
        *,
        instance_id: UUID,
        decision: WorkflowStatus,
        actor_user_id: int,
        remarks: str | None = None,
    ) -> dict[str, Any]:
        inst = self.db.get(WorkflowInstance, instance_id)
        if not inst or inst.is_deleted:
            raise ValueError("Workflow instance not found")
        if inst.status in (WorkflowStatus.APPROVED, WorkflowStatus.REJECTED, WorkflowStatus.CANCELLED):
            raise ValueError("Workflow already completed")

        step = self.db.scalar(
            select(WorkflowInstanceStep).where(
                WorkflowInstanceStep.workflow_instance_id == inst.id,
                WorkflowInstanceStep.step_order == inst.current_step_order,
                WorkflowInstanceStep.is_deleted.is_(False),
            )
        )
        if not step:
            raise ValueError("Current workflow step not found")

        step.status = decision
        step.acted_at = datetime.now(timezone.utc)
        step.remarks = remarks
        step.updated_by = actor_user_id

        if decision == WorkflowStatus.REJECTED:
            inst.status = WorkflowStatus.REJECTED
            inst.decided_at = datetime.now(timezone.utc)
            inst.decision_notes = remarks
        else:
            next_step = self.db.scalar(
                select(WorkflowInstanceStep).where(
                    WorkflowInstanceStep.workflow_instance_id == inst.id,
                    WorkflowInstanceStep.step_order == inst.current_step_order + 1,
                    WorkflowInstanceStep.is_deleted.is_(False),
                )
            )
            if next_step:
                inst.current_step_order += 1
                inst.status = WorkflowStatus.PENDING
            else:
                inst.status = WorkflowStatus.APPROVED
                inst.decided_at = datetime.now(timezone.utc)
                inst.decision_notes = remarks

        inst.updated_by = actor_user_id
        self.db.commit()
        return {
            "instance_id": str(inst.id),
            "status": _enum(inst.status),
            "current_step_order": inst.current_step_order,
        }

    # ── Notification Center ──────────────────────────────────────────────────

    def dispatch_notification(
        self,
        *,
        title: str,
        body: str,
        restaurant_id: UUID | None,
        category: NotificationCategory = NotificationCategory.INFORMATION,
        channels: list[DeliveryChannel] | None = None,
        recipient_user_id: int | None = None,
        actor_user_id: int | None = None,
    ) -> dict[str, Any]:
        channels = channels or [DeliveryChannel.IN_APP]
        in_app = self.notifications.create(
            title=title,
            body=body,
            notification_type=NotificationType.ALERT if category == NotificationCategory.CRITICAL else NotificationType.INFO,
            user_id=recipient_user_id,
            restaurant_id=restaurant_id,
        )
        notif_id = UUID(in_app["id"])

        deliveries = []
        now = datetime.now(timezone.utc)
        for channel in channels:
            status = "SENT" if channel == DeliveryChannel.IN_APP else "QUEUED"
            row = NotificationDelivery(
                notification_id=notif_id,
                restaurant_id=restaurant_id,
                recipient_user_id=recipient_user_id,
                category=category,
                channel=channel,
                subject=title,
                body=body,
                status=status,
                sent_at=now if channel == DeliveryChannel.IN_APP else None,
                provider_response={"note": "placeholder provider adapter"},
                created_by=actor_user_id,
                updated_by=actor_user_id,
            )
            self.db.add(row)
            deliveries.append(row)
        self.db.commit()

        return {
            "notification_id": in_app["id"],
            "channels": [c.value for c in channels],
            "delivery_statuses": [d.status for d in deliveries],
        }

    def list_delivery_log(self, limit: int = 100) -> list[dict[str, Any]]:
        rows = self.db.scalars(
            select(NotificationDelivery)
            .where(NotificationDelivery.is_deleted.is_(False))
            .order_by(NotificationDelivery.created_at.desc())
            .limit(limit)
        ).all()
        return [
            _to_out(
                row,
                [
                    "id",
                    "notification_id",
                    "channel",
                    "category",
                    "status",
                    "sent_at",
                    "recipient_user_id",
                    "created_at",
                ],
            )
            for row in rows
        ]

    # ── Jobs / Scheduler ─────────────────────────────────────────────────────

    def list_jobs(self, restaurant_id: UUID) -> list[dict[str, Any]]:
        rows = self.db.scalars(
            select(JobDefinition)
            .where(JobDefinition.restaurant_id == restaurant_id, JobDefinition.is_deleted.is_(False))
            .order_by(JobDefinition.name.asc())
        ).all()
        return [
            _to_out(
                row,
                [
                    "id",
                    "name",
                    "code",
                    "schedule_cron",
                    "timezone",
                    "enabled",
                    "paused",
                    "max_retries",
                    "last_run_at",
                    "next_run_at",
                ],
            )
            for row in rows
        ]

    def upsert_job(
        self,
        *,
        restaurant_id: UUID,
        name: str,
        code: str,
        schedule_cron: str | None,
        timezone_name: str,
        max_retries: int,
        config: dict[str, Any] | None,
        actor_user_id: int | None,
    ) -> dict[str, Any]:
        row = self.db.scalar(
            select(JobDefinition).where(
                JobDefinition.restaurant_id == restaurant_id,
                JobDefinition.code == code,
                JobDefinition.is_deleted.is_(False),
            )
        )
        if not row:
            row = JobDefinition(
                restaurant_id=restaurant_id,
                name=name,
                code=code,
                created_by=actor_user_id,
            )
            self.db.add(row)
        row.name = name
        row.schedule_cron = schedule_cron
        row.timezone = timezone_name
        row.max_retries = max_retries
        row.config = config or {}
        row.updated_by = actor_user_id
        self.db.commit()
        return {"id": str(row.id), "name": row.name, "code": row.code}

    def set_job_paused(self, job_id: UUID, paused: bool, actor_user_id: int | None) -> dict[str, Any]:
        row = self.db.get(JobDefinition, job_id)
        if not row or row.is_deleted:
            raise ValueError("Job definition not found")
        row.paused = paused
        row.updated_by = actor_user_id
        self.db.commit()
        return {"id": str(row.id), "paused": row.paused}

    def enqueue_job_run(
        self,
        *,
        job_id: UUID,
        trigger_type: str,
        actor_user_id: int | None,
    ) -> dict[str, Any]:
        row = self.db.get(JobDefinition, job_id)
        if not row or row.is_deleted:
            raise ValueError("Job definition not found")
        run = JobRun(
            job_definition_id=row.id,
            run_status=JobRunStatus.QUEUED,
            trigger_type=trigger_type,
            attempt_no=1,
            created_by=actor_user_id,
            updated_by=actor_user_id,
        )
        self.db.add(run)
        self.db.commit()
        return {"run_id": str(run.id), "job_id": str(row.id), "status": _enum(run.run_status)}

    def execute_job_run(self, run_id: UUID) -> None:
        """Synchronous execution body; intended to run in BackgroundTasks."""
        run = self.db.get(JobRun, run_id)
        if not run or run.is_deleted:
            return
        job = self.db.get(JobDefinition, run.job_definition_id)
        if not job or job.is_deleted or not job.enabled:
            run.run_status = JobRunStatus.CANCELLED
            run.error_message = "Job disabled or missing"
            self.db.commit()
            return

        started = time.perf_counter()
        run.run_status = JobRunStatus.RUNNING
        run.started_at = datetime.now(timezone.utc)
        self.db.commit()

        try:
            payload = self._execute_job_code(job.code, restaurant_id=job.restaurant_id, config=job.config or {})
            duration_ms = int((time.perf_counter() - started) * 1000)
            run.run_status = JobRunStatus.SUCCESS
            run.finished_at = datetime.now(timezone.utc)
            run.duration_ms = duration_ms
            run.rows_processed = int(payload.get("rows_processed", 0))
            run.output_payload = payload
            job.last_run_at = run.finished_at
            job.next_run_at = datetime.now(timezone.utc) + timedelta(hours=24)
        except Exception as exc:  # noqa: BLE001
            run.run_status = JobRunStatus.FAILED
            run.finished_at = datetime.now(timezone.utc)
            run.error_message = str(exc)
        self.db.commit()

    def _execute_job_code(
        self, code: str, *, restaurant_id: UUID, config: dict[str, Any]
    ) -> dict[str, Any]:
        """Minimal deterministic workers; can be expanded to queue workers later."""
        now = datetime.now(timezone.utc)
        if code == "DAILY_REPORT":
            return {"rows_processed": 1, "message": "daily report snapshot generated", "at": now.isoformat()}
        if code == "WEEKLY_REPORT":
            return {"rows_processed": 1, "message": "weekly report snapshot generated", "at": now.isoformat()}
        if code == "MONTHLY_REPORT":
            return {"rows_processed": 1, "message": "monthly report snapshot generated", "at": now.isoformat()}
        if code == "INVENTORY_SCAN":
            rows = self.db.scalar(
                select(func.count()).select_from(FileAsset).where(FileAsset.restaurant_id == restaurant_id)
            )
            return {"rows_processed": int(rows or 0), "message": "inventory scan completed"}
        if code == "DATA_CLEANUP":
            return {"rows_processed": 0, "message": "cleanup pass complete"}
        return {"rows_processed": 0, "message": f"job {code} executed", "config": config}

    def list_job_runs(self, *, job_id: UUID | None = None, limit: int = 200) -> list[dict[str, Any]]:
        stmt = select(JobRun).where(JobRun.is_deleted.is_(False))
        if job_id:
            stmt = stmt.where(JobRun.job_definition_id == job_id)
        rows = self.db.scalars(stmt.order_by(JobRun.created_at.desc()).limit(limit)).all()
        return [
            _to_out(
                row,
                [
                    "id",
                    "job_definition_id",
                    "run_status",
                    "trigger_type",
                    "attempt_no",
                    "started_at",
                    "finished_at",
                    "duration_ms",
                    "rows_processed",
                    "error_message",
                    "created_at",
                ],
            )
            for row in rows
        ]

    # ── Report Scheduler ─────────────────────────────────────────────────────

    def upsert_report_schedule(
        self,
        *,
        schedule_id: UUID | None,
        restaurant_id: UUID,
        created_by_user_id: int | None,
        report_kind: str,
        frequency: str,
        delivery_channel: DeliveryChannel,
        export_format: str,
        recipients: dict[str, Any] | None,
        filters: dict[str, Any] | None,
    ) -> dict[str, Any]:
        row = self.db.get(ReportSchedule, schedule_id) if schedule_id else None
        if row is None:
            row = ReportSchedule(
                restaurant_id=restaurant_id,
                created_by_user_id=created_by_user_id,
                report_kind=report_kind,
                frequency=frequency,
                delivery_channel=delivery_channel,
                export_format=export_format,
                recipients=recipients or {},
                filters=filters or {},
                next_send_at=datetime.now(timezone.utc) + timedelta(days=1),
                created_by=created_by_user_id,
                updated_by=created_by_user_id,
            )
            self.db.add(row)
        else:
            row.report_kind = report_kind
            row.frequency = frequency
            row.delivery_channel = delivery_channel
            row.export_format = export_format
            row.recipients = recipients or {}
            row.filters = filters or {}
            row.updated_by = created_by_user_id
        self.db.commit()
        return _to_out(
            row,
            [
                "id",
                "report_kind",
                "frequency",
                "delivery_channel",
                "export_format",
                "enabled",
                "next_send_at",
            ],
        )

    def list_report_schedules(self, restaurant_id: UUID) -> list[dict[str, Any]]:
        rows = self.db.scalars(
            select(ReportSchedule)
            .where(ReportSchedule.restaurant_id == restaurant_id, ReportSchedule.is_deleted.is_(False))
            .order_by(ReportSchedule.created_at.desc())
        ).all()
        return [
            _to_out(
                row,
                [
                    "id",
                    "report_kind",
                    "frequency",
                    "delivery_channel",
                    "export_format",
                    "enabled",
                    "last_sent_at",
                    "next_send_at",
                ],
            )
            for row in rows
        ]

    # ── System Settings / Files / API Mgmt / Integrations ───────────────────

    def set_setting(
        self,
        *,
        scope_type: str,
        scope_id: str | None,
        setting_key: str,
        setting_value: dict[str, Any],
        actor_user_id: int | None,
        is_secret: bool = False,
    ) -> dict[str, Any]:
        row = self.db.scalar(
            select(SystemSetting).where(
                SystemSetting.scope_type == scope_type,
                SystemSetting.scope_id == scope_id,
                SystemSetting.setting_key == setting_key,
                SystemSetting.is_deleted.is_(False),
            )
        )
        if row is None:
            row = SystemSetting(
                scope_type=scope_type,
                scope_id=scope_id,
                setting_key=setting_key,
                setting_value=setting_value,
                is_secret=is_secret,
                created_by=actor_user_id,
                updated_by=actor_user_id,
            )
            self.db.add(row)
        else:
            row.setting_value = setting_value
            row.is_secret = is_secret
            row.updated_by = actor_user_id
        self.db.commit()
        return _to_out(row, ["id", "scope_type", "scope_id", "setting_key", "is_secret", "updated_at"])

    def list_settings(self, scope_type: str | None = None) -> list[dict[str, Any]]:
        stmt = select(SystemSetting).where(SystemSetting.is_deleted.is_(False))
        if scope_type:
            stmt = stmt.where(SystemSetting.scope_type == scope_type)
        rows = self.db.scalars(stmt.order_by(SystemSetting.updated_at.desc())).all()
        return [
            {
                **_to_out(row, ["id", "scope_type", "scope_id", "setting_key", "value_type", "is_secret", "updated_at"]),
                "setting_value": None if row.is_secret else row.setting_value,
            }
            for row in rows
        ]

    def register_file_asset(
        self,
        *,
        restaurant_id: UUID | None,
        branch_id: UUID | None,
        uploaded_by_user_id: int | None,
        category: str,
        file_name: str,
        storage_path: str,
        mime_type: str | None,
        file_size_bytes: int,
        checksum: str | None,
        metadata_json: dict[str, Any] | None,
    ) -> dict[str, Any]:
        row = FileAsset(
            restaurant_id=restaurant_id,
            branch_id=branch_id,
            uploaded_by_user_id=uploaded_by_user_id,
            category=category,
            file_name=file_name,
            storage_path=storage_path,
            mime_type=mime_type,
            file_size_bytes=file_size_bytes,
            checksum=checksum,
            metadata_json=metadata_json or {},
            created_by=uploaded_by_user_id,
            updated_by=uploaded_by_user_id,
        )
        self.db.add(row)
        self.db.commit()
        return _to_out(
            row,
            ["id", "category", "file_name", "storage_path", "mime_type", "file_size_bytes", "created_at"],
        )

    def list_file_assets(self, restaurant_id: UUID | None = None, limit: int = 200) -> list[dict[str, Any]]:
        stmt = select(FileAsset).where(FileAsset.is_deleted.is_(False))
        if restaurant_id:
            stmt = stmt.where(FileAsset.restaurant_id == restaurant_id)
        rows = self.db.scalars(stmt.order_by(FileAsset.created_at.desc()).limit(limit)).all()
        return [
            _to_out(
                row,
                [
                    "id",
                    "restaurant_id",
                    "branch_id",
                    "category",
                    "file_name",
                    "storage_path",
                    "file_size_bytes",
                    "created_at",
                ],
            )
            for row in rows
        ]

    def create_api_key(
        self,
        *,
        restaurant_id: UUID | None,
        name: str,
        scopes: dict[str, Any] | None,
        requests_per_minute: int,
        actor_user_id: int | None,
    ) -> dict[str, Any]:
        raw_secret = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(raw_secret.encode("utf-8")).hexdigest()
        key_id = f"rk_{secrets.token_hex(8)}"
        row = ApiCredential(
            restaurant_id=restaurant_id,
            name=name,
            key_id=key_id,
            key_hash=key_hash,
            status=ApiKeyStatus.ACTIVE,
            scopes=scopes or {"*": True},
            requests_per_minute=requests_per_minute,
            created_by=actor_user_id,
            updated_by=actor_user_id,
        )
        self.db.add(row)
        self.db.commit()
        return {
            "id": str(row.id),
            "name": row.name,
            "key_id": row.key_id,
            "secret_once": raw_secret,
            "requests_per_minute": row.requests_per_minute,
        }

    def list_api_keys(self, restaurant_id: UUID | None = None) -> list[dict[str, Any]]:
        stmt = select(ApiCredential).where(ApiCredential.is_deleted.is_(False))
        if restaurant_id:
            stmt = stmt.where(ApiCredential.restaurant_id == restaurant_id)
        rows = self.db.scalars(stmt.order_by(ApiCredential.created_at.desc())).all()
        return [
            _to_out(
                row,
                ["id", "name", "key_id", "status", "requests_per_minute", "last_used_at", "expires_at", "created_at"],
            )
            for row in rows
        ]

    def create_webhook(
        self,
        *,
        restaurant_id: UUID | None,
        name: str,
        url: str,
        subscribed_events: list[str],
        actor_user_id: int | None,
    ) -> dict[str, Any]:
        secret = secrets.token_urlsafe(24)
        row = WebhookEndpoint(
            restaurant_id=restaurant_id,
            name=name,
            url=url,
            secret_hash=hashlib.sha256(secret.encode("utf-8")).hexdigest(),
            subscribed_events=subscribed_events,
            is_active=True,
            created_by=actor_user_id,
            updated_by=actor_user_id,
        )
        self.db.add(row)
        self.db.commit()
        return {"id": str(row.id), "name": row.name, "url": row.url, "secret_once": secret}

    def list_webhooks(self, restaurant_id: UUID | None = None) -> list[dict[str, Any]]:
        stmt = select(WebhookEndpoint).where(WebhookEndpoint.is_deleted.is_(False))
        if restaurant_id:
            stmt = stmt.where(WebhookEndpoint.restaurant_id == restaurant_id)
        rows = self.db.scalars(stmt.order_by(WebhookEndpoint.created_at.desc())).all()
        return [
            _to_out(row, ["id", "name", "url", "is_active", "failure_count", "last_delivered_at", "created_at"])
            for row in rows
        ]

    def upsert_integration(
        self,
        *,
        restaurant_id: UUID,
        provider: str,
        status: str,
        config: dict[str, Any] | None,
        actor_user_id: int | None,
    ) -> dict[str, Any]:
        row = self.db.scalar(
            select(IntegrationConnector).where(
                IntegrationConnector.restaurant_id == restaurant_id,
                IntegrationConnector.provider == provider,
                IntegrationConnector.is_deleted.is_(False),
            )
        )
        if row is None:
            row = IntegrationConnector(
                restaurant_id=restaurant_id,
                provider=provider,
                status=status,
                config=config or {},
                created_by=actor_user_id,
                updated_by=actor_user_id,
            )
            self.db.add(row)
        else:
            row.status = status
            row.config = config or {}
            row.updated_by = actor_user_id
        self.db.commit()
        return _to_out(row, ["id", "provider", "status", "last_sync_at", "health_score", "last_error"])

    def list_integrations(self, restaurant_id: UUID) -> list[dict[str, Any]]:
        rows = self.db.scalars(
            select(IntegrationConnector)
            .where(IntegrationConnector.restaurant_id == restaurant_id, IntegrationConnector.is_deleted.is_(False))
            .order_by(IntegrationConnector.provider.asc())
        ).all()
        return [
            _to_out(row, ["id", "provider", "status", "last_sync_at", "health_score", "last_error"]) for row in rows
        ]

    # ── Audit / Security / Health / Dashboard ───────────────────────────────

    def list_audit_logs(self, limit: int = 300) -> list[dict[str, Any]]:
        from app.models import AuditLog

        rows = self.db.scalars(
            select(AuditLog).where(AuditLog.is_deleted.is_(False)).order_by(AuditLog.created_at.desc()).limit(limit)
        ).all()
        return [
            _to_out(
                row,
                ["id", "actor_user_id", "action", "entity_type", "entity_id", "details", "ip_address", "created_at"],
            )
            for row in rows
        ]

    def record_login_event(
        self,
        *,
        user_id: int | None,
        event_type: str,
        success: bool,
        ip_address: str | None,
        user_agent: str | None,
        message: str | None = None,
    ) -> None:
        self.db.add(
            LoginEvent(
                user_id=user_id,
                event_type=event_type,
                success=success,
                ip_address=ip_address,
                user_agent=user_agent,
                message=message,
            )
        )
        self.db.commit()

    def create_security_alert(
        self,
        *,
        restaurant_id: UUID | None,
        user_id: int | None,
        severity: SecuritySeverity,
        alert_type: str,
        title: str,
        body: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        row = SecurityAlert(
            restaurant_id=restaurant_id,
            user_id=user_id,
            severity=severity,
            alert_type=alert_type,
            title=title,
            body=body,
            payload=payload or {},
        )
        self.db.add(row)
        self.db.commit()
        return _to_out(row, ["id", "severity", "alert_type", "title", "is_resolved", "created_at"])

    def security_overview(self) -> dict[str, Any]:
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        active_sessions = self.db.scalar(
            select(func.count())
            .select_from(UserSession)
            .where(UserSession.is_deleted.is_(False), UserSession.revoked.is_(False), UserSession.logged_out_at.is_(None))
        )
        failed_logins = self.db.scalar(
            select(func.count())
            .select_from(LoginEvent)
            .where(LoginEvent.created_at >= seven_days_ago, LoginEvent.success.is_(False), LoginEvent.is_deleted.is_(False))
        )
        open_alerts = self.db.scalar(
            select(func.count())
            .select_from(SecurityAlert)
            .where(SecurityAlert.is_deleted.is_(False), SecurityAlert.is_resolved.is_(False))
        )
        return {
            "active_sessions": int(active_sessions or 0),
            "failed_logins_7d": int(failed_logins or 0),
            "open_security_alerts": int(open_alerts or 0),
        }

    def system_health(self) -> dict[str, Any]:
        t0 = time.perf_counter()
        self.db.execute(select(1))
        db_ms = int((time.perf_counter() - t0) * 1000)
        storage_used_bytes = self.db.scalar(
            select(func.coalesce(func.sum(FileAsset.file_size_bytes), 0)).where(FileAsset.is_deleted.is_(False))
        )
        queued_jobs = self.db.scalar(
            select(func.count()).select_from(JobRun).where(JobRun.run_status == JobRunStatus.QUEUED, JobRun.is_deleted.is_(False))
        )
        failed_jobs = self.db.scalar(
            select(func.count()).select_from(JobRun).where(JobRun.run_status == JobRunStatus.FAILED, JobRun.is_deleted.is_(False))
        )
        return {
            "database": {"status": "ok", "latency_ms": db_ms},
            "storage": {"tracked_file_bytes": int(storage_used_bytes or 0)},
            "jobs": {"queued": int(queued_jobs or 0), "failed": int(failed_jobs or 0)},
            "api": {"status": "ok"},
        }

    def admin_dashboard(self) -> dict[str, Any]:
        running_jobs = self.db.scalar(
            select(func.count()).select_from(JobRun).where(JobRun.run_status == JobRunStatus.RUNNING, JobRun.is_deleted.is_(False))
        )
        failed_jobs = self.db.scalar(
            select(func.count()).select_from(JobRun).where(JobRun.run_status == JobRunStatus.FAILED, JobRun.is_deleted.is_(False))
        )
        unread_notifications = self.db.scalar(
            select(func.count()).select_from(Notification).where(Notification.is_read.is_(False), Notification.is_deleted.is_(False))
        )
        recent_activities = self.list_audit_logs(limit=10)
        return {
            "running_jobs": int(running_jobs or 0),
            "failed_jobs": int(failed_jobs or 0),
            "unread_notifications": int(unread_notifications or 0),
            "system_health": self.system_health(),
            "recent_activity": recent_activities,
        }

    # ── Seed / Defaults ──────────────────────────────────────────────────────

    def bootstrap_default_jobs(self, restaurant_id: UUID, actor_user_id: int | None = None) -> int:
        defaults = [
            ("Daily Reports", "DAILY_REPORT", "0 1 * * *"),
            ("Weekly Reports", "WEEKLY_REPORT", "0 2 * * 1"),
            ("Monthly Reports", "MONTHLY_REPORT", "0 3 1 * *"),
            ("Inventory Scan", "INVENTORY_SCAN", "0 */6 * * *"),
            ("Expiry Check", "EXPIRY_CHECK", "15 4 * * *"),
            ("Payroll Processing", "PAYROLL_PROCESSING", "0 6 1 * *"),
            ("Reservation Reminder", "RESERVATION_REMINDER", "*/20 * * * *"),
            ("Birthday Reminder", "BIRTHDAY_REMINDER", "0 9 * * *"),
            ("Data Cleanup", "DATA_CLEANUP", "30 3 * * *"),
            ("Analytics Aggregation", "ANALYTICS_AGGREGATION", "0 */2 * * *"),
        ]
        created = 0
        for name, code, cron in defaults:
            exists = self.db.scalar(
                select(JobDefinition).where(
                    JobDefinition.restaurant_id == restaurant_id,
                    JobDefinition.code == code,
                    JobDefinition.is_deleted.is_(False),
                )
            )
            if exists:
                continue
            self.db.add(
                JobDefinition(
                    restaurant_id=restaurant_id,
                    name=name,
                    code=code,
                    schedule_cron=cron,
                    timezone="Asia/Kolkata",
                    enabled=True,
                    paused=False,
                    max_retries=3,
                    config={},
                    created_by=actor_user_id,
                    updated_by=actor_user_id,
                )
            )
            created += 1
        self.db.commit()
        return created

