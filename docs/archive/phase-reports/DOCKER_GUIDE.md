# Docker Guide

## Images

| Image | Dockerfile | Role |
|-------|------------|------|
| API | `Backend/Dockerfile` | Uvicorn FastAPI |
| Worker | `Backend/Dockerfile.worker` | Celery worker (override CMD for beat) |
| Frontend | `Frontend/Dockerfile` | Vite build + nginx static |
| Postgres | `postgres:16-alpine` | Primary database |
| Redis | `redis:7-alpine` | Cache + broker |
| Edge | `nginx:1.27-alpine` | Reverse proxy |

## Compose services

`docker-compose.yml` defines: `postgres`, `redis`, `backend`, `worker`, `scheduler`, `frontend`, `nginx`, and optional `migrate` (profile).

```bash
docker compose up --build
docker compose logs -f backend worker
docker compose --profile migrate run --rm migrate
docker compose down
```

## Healthchecks

- Postgres: `pg_isready`
- Redis: `redis-cli ping`
- Backend: `GET /health/live`
- Nginx: proxies `/health/live`

## Building independently

```bash
docker build -t rrps-backend ./Backend
docker build -f Backend/Dockerfile.worker -t rrps-worker ./Backend
docker build -t rrps-frontend ./Frontend --build-arg VITE_API_BASE_URL=/api/v1
```

## Volumes

- `postgres_data`, `redis_data`
- `backend_uploads`, `backend_logs`, `backend_backups`

## Notes

- Multi-stage builds keep runtime images slim.
- Frontend bakes `VITE_API_BASE_URL` at build time (default `/api/v1` behind nginx).
- Worker and API share the same Python dependencies; only the entrypoint differs.
