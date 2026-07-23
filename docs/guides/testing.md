# Testing Guide

## Backend

```bash
cd Backend
pip install -r requirements.txt
pytest -q --tb=short
```

CI runs migrations against Postgres + Redis service containers, then pytest.

### Suites (high level)

| Area | Files |
|------|-------|
| Health | `test_health.py`, `test_api_health.py` |
| Auth security | `test_auth_security.py` |
| Cache / storage / queue | `test_cache_service.py`, `test_storage_service.py`, `test_queue_tasks.py` |
| Domain smoke | `test_inventory_pos_analytics_smoke.py` |
| ML / planning | `test_learning.py`, `test_persistence.py`, `test_recommendation.py` |

## Frontend

```bash
cd Frontend
npm ci
npm run lint
npm run build
```

## Docker

CI builds `Backend`, `Backend/Dockerfile.worker`, and `Frontend` images without pushing.

## Gaps (tracked for 1.1.0)

- Broader API integration matrix
- Frontend E2E (Playwright)
- Contract tests against OpenAPI
