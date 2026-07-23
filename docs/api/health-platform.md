# Health & Platform API

## Health

### GET `/api/v1/health`

| Field | Value |
|-------|--------|
| **Description** | Basic process health |
| **Authentication** | Public |
| **Request** | None |
| **Response** | `{ "status": "ok" }` |
| **Status codes** | `200` |

### GET `/api/v1/health/live`

| Field | Value |
|-------|--------|
| **Description** | Kubernetes/ECS liveness probe |
| **Authentication** | Public |
| **Status codes** | `200` |

**Example**

```bash
curl -s http://localhost:8000/api/v1/health/live
# {"status":"ok"}
```

### GET `/api/v1/health/ready`

| Field | Value |
|-------|--------|
| **Description** | Readiness (DB / Redis checks) |
| **Authentication** | Public |
| **Status codes** | `200`, `503` |

### GET `/api/v1/health/detailed`

| Field | Value |
|-------|--------|
| **Description** | Component-level health detail |
| **Authentication** | Public |
| **Status codes** | `200` |

### GET `/metrics`

| Field | Value |
|-------|--------|
| **Description** | Prometheus metrics (app root, not under `/api/v1`) |
| **Authentication** | Public |
| **Status codes** | `200` |

---

## Platform ops (`/api/v1/platform`)

All platform routes require JWT + elevated roles unless noted.

| Method | URL | Description | Auth | Status codes |
|--------|-----|-------------|------|--------------|
| GET | `/platform/health-center` | Aggregated ops health | Roles | 200, 401, 403 |
| GET | `/platform/deployment` | Deployment metadata | ADMIN+ | 200, 401, 403 |
| GET | `/platform/migrations` | Alembic migration status | ADMIN+ | 200, 401, 403 |
| GET | `/platform/cache` | Cache backend status | ADMIN+ | 200, 401, 403 |
| POST | `/platform/cache/clear` | Flush cache namespace | ADMIN+ | 200, 401, 403 |
| POST | `/platform/cache/set` | Set cache key | ADMIN+ | 200, 400, 401, 403 |
| GET | `/platform/cache/get` | Get cache key | ADMIN+ | 200, 404, 401, 403 |
| GET | `/platform/queue` | Celery queue overview | Roles | 200, 401, 403 |
| POST | `/platform/queue/enqueue` | Enqueue named task | ADMIN+ | 200, 400, 401, 403 |
| GET | `/platform/queue/tasks/{task_id}` | Task result/status | Roles | 200, 404, 401, 403 |
| GET | `/platform/logs` | Recent application logs | ADMIN+ | 200, 401, 403 |
| GET | `/platform/monitoring` | CPU/mem/process metrics | Roles | 200, 401, 403 |
| GET | `/platform/backups` | List backup artifacts | ADMIN+ | 200, 401, 403 |
| POST | `/platform/backups/run` | Trigger backup | SUPER_ADMIN | 200, 401, 403 |
| POST | `/platform/backups/prune` | Prune old backups | SUPER_ADMIN | 200, 401, 403 |
| GET | `/platform/storage` | Storage backend status | ADMIN+ | 200, 401, 403 |

### Example — enqueue

**Request**

```json
{
  "task": "app.tasks.notifications.send_test",
  "args": [],
  "kwargs": {}
}
```

**Response `200`**

```json
{ "task_id": "b3c1…", "status": "PENDING" }
```

```bash
curl -X POST "$API/platform/queue/enqueue" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"task":"app.tasks.notifications.send_test"}'
```
