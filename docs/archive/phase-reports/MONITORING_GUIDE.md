# Monitoring Guide

## Health endpoints

| Path | Purpose | Expected |
|------|---------|----------|
| `/health` | Legacy liveness | `{"status":"ok"}` |
| `/health/live` | K8s/Docker liveness | 200 |
| `/health/ready` | Readiness (DB/Redis/storage) | 200 or 503 |
| `/health/detailed` | Full dependency + resources | JSON |
| `/metrics` | Prometheus text | when enabled |

## Platform APIs (authenticated)

- `GET /api/v1/platform/monitoring`
- `GET /api/v1/platform/health-center`
- `GET /api/v1/platform/queue`
- `GET /api/v1/platform/logs`
- `GET /api/v1/platform/deployment`

## Frontend dashboards

Platform Ops section: System Monitoring, Health Center, Queue Monitor, Log Viewer, Deployment Status, Backup Center.

## Logs

- `LOG_FORMAT=json` in staging/production
- Every request emits `api_request` / `api_response` with `request_id`
- Responses include `X-Request-ID` and `X-Response-Time-Ms`
- Ship container stdout to CloudWatch / Azure Monitor / Stackdriver / Loki

## Metrics & tracing

- Prometheus scrape `/metrics` (CPU, memory, disk gauges + request counters)
- Optional Sentry via `SENTRY_DSN`
- Nginx edge rate zone + security headers

## Alert suggestions

| Alert | Condition |
|-------|-----------|
| API down | `/health/live` failing 2m |
| Not ready | `/health/ready` 503 for 5m |
| High latency | p95 `duration_ms` > 500 |
| Queue backlog | `default_queue_depth` > 1000 |
| Disk | disk percent > 85 |
| Backup stale | no successful backup in 36h |
