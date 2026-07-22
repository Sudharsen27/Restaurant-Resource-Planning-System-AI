# Environment Variables

Templates live in `env/` and `Backend/.env.example`. Copy to `.env` locally; inject via secrets managers in cloud.

## Application

| Variable | Default | Notes |
|----------|---------|-------|
| `APP_ENV` | `development` | `development` / `testing` / `staging` / `production` |
| `DEBUG` | `true` | Must be `false` in production |
| `LOG_LEVEL` | `INFO` | |
| `LOG_FORMAT` | `text` | Use `json` in prod |
| `APP_VERSION` | `1.0.0` | |

## Database

| Variable | Notes |
|----------|-------|
| `DATABASE_URL` | `postgresql://...` required |
| `DB_POOL_SIZE` / `DB_MAX_OVERFLOW` / `DB_POOL_RECYCLE` | Connection pooling |
| `DB_STATEMENT_TIMEOUT_SECONDS` | Soft query timeout |
| `USE_ALEMBIC` | Prefer `true` |
| `ALLOW_CREATE_ALL` | `false` in prod |
| `SEED_ENTERPRISE_DATA` | Demo seed; `false` in prod |

## Security

| Variable | Notes |
|----------|-------|
| `SECRET_KEY` | Strong random; never commit |
| `JWT_ACCESS_EXPIRE_MINUTES` | Access token TTL |
| `JWT_REFRESH_EXPIRE_DAYS` | Refresh TTL (rotation enabled in auth service) |
| `PASSWORD_MIN_LENGTH` | Policy floor |
| `RATE_LIMIT_ENABLED` | Redis-backed when Redis up |
| `CSP_ENABLED` / `HSTS_ENABLED` / `HTTPS_REDIRECT_ENABLED` / `CSRF_ENABLED` | Hardening toggles |

## Redis & Celery

| Variable | Notes |
|----------|-------|
| `REDIS_URL` | Cache / sessions / rate limit |
| `REDIS_ENABLED` | Fallback to memory if false/unreachable |
| `CELERY_BROKER_URL` | Queue broker |
| `CELERY_RESULT_BACKEND` | Task results |
| `CELERY_TASK_ALWAYS_EAGER` | `true` in tests |

## Storage

| Variable | Notes |
|----------|-------|
| `STORAGE_BACKEND` | `local` \| `s3` \| `r2` \| `azure` \| `gcs` |
| `S3_BUCKET` / `S3_ENDPOINT_URL` | S3 or R2 |
| `AWS_*` | Prefer IAM roles |
| `AZURE_STORAGE_*` | Blob |
| `GCS_BUCKET` / `GCS_CREDENTIALS_JSON` | GCS |

## Observability & backups

| Variable | Notes |
|----------|-------|
| `SENTRY_DSN` | Error tracking |
| `METRICS_ENABLED` | Prometheus `/metrics` |
| `BACKUP_DIR` / `BACKUP_RETENTION_DAYS` | Dump location & prune |
| `DEPLOYMENT_ID` / `GIT_SHA` / `BUILD_TIMESTAMP` | Surfaced in deployment UI |

## Frontend

| Variable | Notes |
|----------|-------|
| `VITE_API_BASE_URL` | e.g. `/api/v1` or `http://127.0.0.1:8000/api/v1` |
| `VITE_API_TIMEOUT_MS` | Axios timeout |

## Secret management

- **AWS** Secrets Manager / SSM Parameter Store
- **Azure** Key Vault
- **GCP** Secret Manager
- **Self-hosted** HashiCorp Vault or encrypted sops files (not in git)
