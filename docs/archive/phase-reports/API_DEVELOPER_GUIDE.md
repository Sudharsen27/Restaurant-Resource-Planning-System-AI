# API Developer Guide

## Base URL

- Local Vite: `http://127.0.0.1:8000/api/v1` (or your `VITE_API_BASE_URL`)
- Compose/nginx: `http://localhost/api/v1`

## Interactive docs

- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI JSON: `/openapi.json`

## Conventions

- Versioned routes under `/api/v1`
- Many responses wrap `{ success, data }` (platform/admin)
- Health routes return plain status payloads
- Propagate `X-Request-ID` for support traces

## Platform ops (Phase 12)

Prefix: `/api/v1/platform`

Requires roles `SUPER_ADMIN` / `ADMIN` (some endpoints also `MANAGER`).

Examples: health-center, monitoring, cache, queue, logs, migrations, backups, deployment, storage.

## Background jobs

Enqueue via `POST /api/v1/platform/queue/enqueue`:

```json
{ "job_type": "email", "payload": { "to": "a@b.com", "subject": "Hi", "body": "..." } }
```

Job types: `email`, `report`, `inventory_check`, `notification`, `analytics`.

## Storage

Configure `STORAGE_BACKEND`. Uploads go through `StorageService` (local path or cloud object key + URL).
