# Deployment Guide

## Prerequisites

- Docker 24+ and Docker Compose v2
- PostgreSQL 16 (or Compose service)
- Redis 7 (or Compose service)
- Secrets manager for staging/production (`SECRET_KEY`, `DATABASE_URL`, storage credentials)

## Local (Compose)

1. Copy `env/development.env.example` values as needed.
2. Set `SECRET_KEY` in the shell or a local `.env` next to Compose (never commit it).
3. Start the stack:

```bash
docker compose up --build
```

4. Run migrations once (safe on empty Postgres — creates schema then stamps Alembic head):

```bash
docker compose --profile migrate run --rm migrate
```

> If a previous migrate attempt failed mid-way, reset the volume first:
> `docker compose down -v` then `docker compose up -d postgres redis` and re-run migrate.

5. Verify:

- `GET http://localhost/health/live`
- `GET http://localhost/health/ready`
- `GET http://localhost/docs`

## Zero-downtime rollout (recommended)

1. **Expand** schema with backward-compatible Alembic migration (additive columns/tables only).
2. Deploy **new API** replicas alongside old ones (rolling update).
3. Drain and restart **Celery workers** after API is healthy.
4. Run **contract** migration only after all old replicas are gone (drop unused columns later).
5. Verify `/health/ready` and `/platform/monitoring` (admin).

## Environment promotion

| Stage | Compose / cluster | Seeds | Rate limit | HTTPS |
|-------|-------------------|-------|------------|-------|
| development | local Compose | on | optional | off |
| testing | CI services | off | off | off |
| staging | managed cluster | off | on | on |
| production | managed cluster | off | on | on |

## Cloud targets

### AWS

- ECS Fargate or EKS for API/worker/scheduler
- RDS PostgreSQL, ElastiCache Redis, S3 storage
- ALB + ACM for TLS; Secrets Manager for `SECRET_KEY` / DB URL

### Azure

- Container Apps or AKS
- Azure Database for PostgreSQL, Azure Cache for Redis, Blob storage
- Key Vault references in app settings

### Google Cloud

- Cloud Run or GKE
- Cloud SQL, Memorystore, GCS
- Secret Manager

### DigitalOcean

- App Platform or Droplets + Compose
- Managed Postgres + Redis
- Spaces (S3-compatible → `STORAGE_BACKEND=s3` + endpoint)

### Self-hosted Linux

- Docker Compose on a VM behind Nginx/Caddy with Let's Encrypt
- Cron: `Backend/scripts/backup_postgres.sh` daily

## Rollback

1. Redeploy previous image tag (`ghcr.io/.../backend:<sha>`).
2. Do **not** automatically downgrade Alembic unless migration is reversible and tested.
3. Restore DB from last verified backup only if data corruption occurred (see Disaster Recovery).
