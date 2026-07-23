# Environment Variables

Templates:

- `env/development.env.example`
- `env/testing.env.example`
- `env/staging.env.example`
- `env/production.env.example`
- `Backend/.env.example`
- `Frontend/.env.example`

**Never commit real `.env` files.**

## Core application

| Variable | Purpose |
|----------|---------|
| `APP_ENV` | `development` / `staging` / `production` |
| `DEBUG` | Disable in production |
| `SECRET_KEY` | JWT signing — strong random in prod |
| `DATABASE_URL` | PostgreSQL URL |
| `CORS_ORIGINS` | Comma-separated allow-list |
| `LOG_LEVEL` / `LOG_FORMAT` | Prefer `json` in prod |

## Auth & security

| Variable | Purpose |
|----------|---------|
| `JWT_ALGORITHM` | Default `HS256` |
| `JWT_ACCESS_EXPIRE_MINUTES` | Access token TTL |
| `JWT_REFRESH_EXPIRE_DAYS` | Refresh TTL |
| `PASSWORD_*` | Password policy |
| `RATE_LIMIT_*` | Rate limiting |
| `CSP_ENABLED` / `HSTS_ENABLED` / `CSRF_ENABLED` | Hardening toggles |
| `HTTPS_REDIRECT_ENABLED` | Honor `X-Forwarded-Proto` |

## Redis & Celery

| Variable | Purpose |
|----------|---------|
| `REDIS_URL` | Cache / sessions |
| `CELERY_BROKER_URL` | Broker |
| `CELERY_RESULT_BACKEND` | Results |
| `CELERY_TASK_ALWAYS_EAGER` | `true` only in tests |

## Storage & observability

| Variable | Purpose |
|----------|---------|
| `STORAGE_BACKEND` | `local` \| `s3` \| `r2` \| `azure` \| `gcs` |
| `S3_BUCKET` / `AWS_REGION` | Object storage |
| `SENTRY_DSN` | Error tracking |
| `METRICS_ENABLED` | Prometheus `/metrics` |
| `BACKUP_DIR` / `BACKUP_RETENTION_DAYS` | Backup policy |

## Frontend (build-time)

| Variable | Purpose |
|----------|---------|
| `VITE_API_BASE_URL` | Usually `/api/v1` behind ALB/nginx |
| `VITE_API_TIMEOUT_MS` | Axios timeout |

## Secrets Manager mapping (AWS)

| Secret key | Env |
|------------|-----|
| `database_url` | `DATABASE_URL` |
| `secret_key` | `SECRET_KEY` |
| `redis_url` | `REDIS_URL` |
| `celery_broker_url` | `CELERY_BROKER_URL` |
| `celery_result_backend` | `CELERY_RESULT_BACKEND` |
