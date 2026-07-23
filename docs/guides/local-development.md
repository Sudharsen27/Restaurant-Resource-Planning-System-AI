# Local Development Guide

## Option A — Docker Compose (recommended)

```bash
docker compose up --build
docker compose --profile migrate run --rm migrate
```

Open http://localhost

## Option B — Hybrid

1. Start Postgres + Redis (Compose or local installs).
2. Backend:

```bash
cd Backend
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # edit DATABASE_URL / REDIS_URL
python scripts/migrate.py
uvicorn app.main:app --reload --port 8000
```

3. Worker (optional):

```bash
celery -A app.celery_app.celery worker --loglevel=INFO
celery -A app.celery_app.celery beat --loglevel=INFO --schedule=/tmp/celerybeat-schedule
```

4. Frontend:

```bash
cd Frontend
npm install
cp .env.example .env
npm run dev
```

## Useful URLs

| URL | Purpose |
|-----|---------|
| http://localhost:5173 | Vite dev server |
| http://localhost:8000/docs | Swagger |
| http://localhost:8000/api/v1/health/live | Liveness |

## Tests

```bash
cd Backend && pytest -q
cd Frontend && npm run lint && npm run build
```
