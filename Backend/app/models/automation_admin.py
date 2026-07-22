"""Phase 10 automation, scheduler, integration, and admin models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import UUIDBaseModel
from app.models.enums import (
    ApiKeyStatus,
    DeliveryChannel,
    JobRunStatus,
    NotificationCategory,
    SecuritySeverity,
    WorkflowEntityType,
    WorkflowStepType,
    WorkflowStatus,
)


class WorkflowDefinition(UUIDBaseModel):
    __tablename__ = "workflow_definitions"
    __table_args__ = (
        UniqueConstraint("restaurant_id", "code", name="uq_workflow_definitions_restaurant_code"),
    )

    restaurant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    code: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    entity_type: Mapped[WorkflowEntityType] = mapped_column(
        Enum(WorkflowEntityType, name="workflowentitytype"),
        nullable=False,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    trigger_event: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class WorkflowStep(UUIDBaseModel):
    __tablename__ = "workflow_steps"
    __table_args__ = (
        UniqueConstraint("workflow_definition_id", "step_order", name="uq_workflow_steps_order"),
    )

    workflow_definition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow_definitions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    step_name: Mapped[str] = mapped_column(String(120), nullable=False)
    step_type: Mapped[WorkflowStepType] = mapped_column(
        Enum(WorkflowStepType, name="workflowsteptype"),
        nullable=False,
    )
    approver_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    approver_user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    sla_minutes: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1440")
    conditions: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class WorkflowInstance(UUIDBaseModel):
    __tablename__ = "workflow_instances"

    workflow_definition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow_definitions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    entity_type: Mapped[WorkflowEntityType] = mapped_column(
        Enum(WorkflowEntityType, name="workflowentitytype"),
        nullable=False,
        index=True,
    )
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    requested_by_user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[WorkflowStatus] = mapped_column(
        Enum(WorkflowStatus, name="workflowstatus"),
        nullable=False,
        server_default=WorkflowStatus.PENDING.value,
        index=True,
    )
    current_step_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    decision_notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class WorkflowInstanceStep(UUIDBaseModel):
    __tablename__ = "workflow_instance_steps"
    __table_args__ = (
        UniqueConstraint("workflow_instance_id", "step_order", name="uq_workflow_instance_steps_order"),
    )

    workflow_instance_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow_instances.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    step_name: Mapped[str] = mapped_column(String(120), nullable=False)
    approver_user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[WorkflowStatus] = mapped_column(
        Enum(WorkflowStatus, name="workflowstatus"),
        nullable=False,
        server_default=WorkflowStatus.PENDING.value,
        index=True,
    )
    acted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)


class NotificationDelivery(UUIDBaseModel):
    __tablename__ = "notification_deliveries"

    notification_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("notifications.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    restaurant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    recipient_user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    category: Mapped[NotificationCategory] = mapped_column(
        Enum(NotificationCategory, name="notificationcategory"),
        nullable=False,
        server_default=NotificationCategory.INFORMATION.value,
    )
    channel: Mapped[DeliveryChannel] = mapped_column(
        Enum(DeliveryChannel, name="deliverychannel"),
        nullable=False,
        server_default=DeliveryChannel.IN_APP.value,
        index=True,
    )
    subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, server_default="QUEUED", index=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    provider_response: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class JobDefinition(UUIDBaseModel):
    __tablename__ = "job_definitions"
    __table_args__ = (
        UniqueConstraint("restaurant_id", "code", name="uq_job_definitions_restaurant_code"),
    )

    restaurant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    schedule_cron: Mapped[str | None] = mapped_column(String(120), nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, server_default="Asia/Kolkata")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true", index=True)
    paused: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false", index=True)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, server_default="3")
    config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class JobRun(UUIDBaseModel):
    __tablename__ = "job_runs"

    job_definition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("job_definitions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    run_status: Mapped[JobRunStatus] = mapped_column(
        Enum(JobRunStatus, name="jobrunstatus"),
        nullable=False,
        server_default=JobRunStatus.QUEUED.value,
        index=True,
    )
    trigger_type: Mapped[str] = mapped_column(String(24), nullable=False, server_default="SCHEDULED")
    attempt_no: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rows_processed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class ReportSchedule(UUIDBaseModel):
    __tablename__ = "report_schedules"

    restaurant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by_user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    report_kind: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    frequency: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    delivery_channel: Mapped[DeliveryChannel] = mapped_column(
        Enum(DeliveryChannel, name="deliverychannel"),
        nullable=False,
        server_default=DeliveryChannel.EMAIL.value,
    )
    export_format: Mapped[str] = mapped_column(String(12), nullable=False, server_default="PDF")
    recipients: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    filters: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true", index=True)
    last_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_send_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SystemSetting(UUIDBaseModel):
    __tablename__ = "system_settings"
    __table_args__ = (
        UniqueConstraint("scope_type", "scope_id", "setting_key", name="uq_system_settings_scope_key"),
    )

    scope_type: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    scope_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    setting_key: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    setting_value: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    value_type: Mapped[str] = mapped_column(String(32), nullable=False, server_default="json")
    is_secret: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")


class FileAsset(UUIDBaseModel):
    __tablename__ = "file_assets"

    restaurant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    branch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("branches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    uploaded_by_user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    category: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
    tags: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class ApiCredential(UUIDBaseModel):
    __tablename__ = "api_credentials"
    __table_args__ = (
        UniqueConstraint("key_id", name="uq_api_credentials_key_id"),
    )

    restaurant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    key_id: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    key_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[ApiKeyStatus] = mapped_column(
        Enum(ApiKeyStatus, name="apikeystatus"),
        nullable=False,
        server_default=ApiKeyStatus.ACTIVE.value,
        index=True,
    )
    scopes: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    requests_per_minute: Mapped[int] = mapped_column(Integer, nullable=False, server_default="120")
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ApiRequestLog(UUIDBaseModel):
    __tablename__ = "api_request_logs"

    api_credential_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("api_credentials.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    response_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    request_meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class WebhookEndpoint(UUIDBaseModel):
    __tablename__ = "webhook_endpoints"

    restaurant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    secret_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    subscribed_events: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true", index=True)
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    last_delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class WebhookDelivery(UUIDBaseModel):
    __tablename__ = "webhook_deliveries"

    webhook_endpoint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("webhook_endpoints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    delivery_status: Mapped[str] = mapped_column(String(24), nullable=False, server_default="QUEUED", index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class IntegrationConnector(UUIDBaseModel):
    __tablename__ = "integration_connectors"
    __table_args__ = (
        UniqueConstraint("restaurant_id", "provider", name="uq_integrations_restaurant_provider"),
    )

    restaurant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, server_default="DISCONNECTED", index=True)
    config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    credentials_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    health_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)


class LoginEvent(UUIDBaseModel):
    __tablename__ = "login_events"

    user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, index=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    device: Mapped[str | None] = mapped_column(String(120), nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)


class SecurityAlert(UUIDBaseModel):
    __tablename__ = "security_alerts"

    restaurant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    severity: Mapped[SecuritySeverity] = mapped_column(
        Enum(SecuritySeverity, name="securityseverity"),
        nullable=False,
        server_default=SecuritySeverity.WARNING.value,
        index=True,
    )
    alert_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false", index=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
