# Deploy with Docker Compose

## Prerequisites

- Docker Engine 24+ and Docker Compose v2
- 4+ GB RAM available to Docker
- Ports `80` (HTTP) and optionally `5432` / `6380` free

## Quick start

```bash
# from repository root
cp env/development.env.example .env   # optional overrides
docker compose up --build -d
docker compose --profile migrate run --rm migrate
```

Application: **http://localhost**  
API health: **http://localhost/api/v1/health/live**  
Swagger (direct backend): map or exec into backend container on `:8000/docs`

## Services

| Service | Image / build | Role |
|---------|---------------|------|
| `postgres` | `postgres:16-alpine` | Database |
| `redis` | `redis:7-alpine` | Cache + Celery |
| `backend` | `Backend/Dockerfile` | FastAPI |
| `worker` | `Backend/Dockerfile.worker` | Celery worker |
| `scheduler` | worker image | Celery beat |
| `frontend` | `Frontend/Dockerfile` | SPA |
| `nginx` | `nginx:1.27-alpine` | Reverse proxy |
| `migrate` | backend image | One-shot Alembic (`--profile migrate`) |

## Useful commands

```bash
docker compose ps
docker compose logs -f backend worker
docker compose --profile migrate run --rm migrate
docker compose down
docker compose down -v   # destroy volumes — destructive
```

## Production-like Compose tips

- Set strong `SECRET_KEY` and `POSTGRES_PASSWORD`
- `SEED_ENTERPRISE_DATA=false`
- `DEBUG=false`, `APP_ENV=production`
- `STORAGE_BACKEND=s3` with real bucket credentials/role
- Terminate TLS at a reverse proxy in front of nginx (or replace nginx with a cloud LB)
- Do not publish Postgres/Redis ports publicly

See also archived guide: [docs/archive/phase-reports/DOCKER_GUIDE.md](../archive/phase-reports/DOCKER_GUIDE.md).
