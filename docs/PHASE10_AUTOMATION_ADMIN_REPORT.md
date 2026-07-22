# Phase 10 — Workflow Automation, Notification Center, Scheduler & Enterprise Administration

## Summary

Phase 10 turns the platform into an enterprise automation control plane with:

- Configurable workflow engine for approvals and custom process orchestration
- Centralized multi-channel notification delivery logging
- Background job definitions, queuing, run history, pause/resume, and manual trigger
- Admin scheduler and report scheduler
- Immutable audit center with security/session signals
- API key and webhook management
- File metadata/storage abstraction registry
- Integration connector registry
- Admin dashboard + health + security dashboards

All persisted on PostgreSQL through FastAPI services.

## Database

New Phase 10 schema objects include:

- `workflow_definitions`, `workflow_steps`, `workflow_instances`, `workflow_instance_steps`
- `notification_deliveries` (reusing existing `notifications` for in-app records)
- `job_definitions`, `job_runs`
- `report_schedules`
- `system_settings`
- `file_assets`
- `api_credentials`, `api_request_logs`
- `webhook_endpoints`, `webhook_deliveries`
- `integration_connectors`
- `login_events`, `security_alerts`

Migration: `ceadafe67267_phase10_automation_admin.py`

## Backend Modules

- `app/services/automation_service.py`
  - Workflow upsert + instance execution
  - Notification dispatch with channel delivery log
  - Job scheduler + background execution
  - Report scheduler
  - Settings/file/api/webhook/integration management
  - Audit, security, and health aggregations
- `app/api/automation_admin.py`
  - `/api/v1/admin/*` endpoints for all admin modules
- `app/api/auth.py`
  - Login/logout/password-change events now recorded in `login_events`

## Frontend Modules

- `Frontend/src/pages/admin/AdminPages.jsx`
  - Admin Console overview
  - Workflow Builder
  - Notification Center
  - Job Scheduler + run history
  - Report Scheduler
  - System Settings
  - Audit Center
  - File Management
  - API Management
  - Integrations
  - Health Dashboard
  - Security Center
- `Frontend/src/services/adminService.js`
  - API client wrappers for Phase 10 admin endpoints
- Navigation and routes updated in:
  - `Frontend/src/constants/navigation.js`
  - `Frontend/src/App.jsx`

## Workflow Engine Design

- Workflow definition (`code`, `entity_type`, trigger) + ordered steps
- Runtime instance per entity request (`entity_id`) with current step pointer
- Step decisions promote to next step or complete/reject flow
- Supports purchase/expense/leave/discount/refund/reservation/custom workflow entities

## Notification Flow

1. Generate in-app notification (`notifications`)
2. Emit one delivery row per target channel (`notification_deliveries`)
3. In-app marks delivered immediately; external channels remain queueable placeholders

## Job Processing Flow

1. Job definition captured with cron + retry metadata
2. Manual/API trigger creates queued `job_runs`
3. FastAPI `BackgroundTasks` executes without blocking request
4. Run row updates status + timing + output payload

## Key API Surface (`/api/v1/admin`)

- Workflows: `GET/POST /workflows`, `POST /workflows/instances`, `POST /workflows/instances/{id}/decision`
- Notifications: `POST /notifications/dispatch`, `GET /notifications/deliveries`
- Jobs: `GET/POST /jobs`, `POST /jobs/bootstrap`, `POST /jobs/{id}/pause`, `POST /jobs/{id}/run-now`, `GET /jobs/runs`
- Report Scheduler: `GET/POST /report-schedules`
- Settings: `GET/POST /settings`
- Files: `GET/POST /files/assets`
- API Mgmt: `GET/POST /api-keys`, `GET/POST /webhooks`
- Integrations: `GET/POST /integrations`
- Audit/Security/Health/Admin: `GET /audit/logs`, `POST /security/alerts`, `GET /security/overview`, `GET /system-health`, `GET /dashboard`

## Testing Checklist

1. Run migration and start backend
2. Bootstrap jobs for a restaurant and run a job manually
3. Create workflow and submit/approve instance
4. Dispatch notification to multi-channel and verify delivery rows
5. Add setting, file metadata, API key, webhook, and integration row
6. Verify admin dashboard counts and health payload
7. Verify login/logout/password-change events appear in security/audit streams
