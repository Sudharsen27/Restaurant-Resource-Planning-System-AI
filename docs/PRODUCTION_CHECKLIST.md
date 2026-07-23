# Production Checklist

Use this gate before exposing RRPS v1.0.x to real customers.

## 1. Secrets & configuration

- [ ] Unique `SECRET_KEY` (≥ 32 random bytes)
- [ ] `DEBUG=false`, `APP_ENV=production`
- [ ] `SEED_ENTERPRISE_DATA=false`
- [ ] `CORS_ORIGINS` limited to real SPA origin(s)
- [ ] DB credentials in Secrets Manager / sealed secret store
- [ ] Redis AUTH + TLS (`rediss://`)
- [ ] No secrets in git, images, or CI logs

## 2. Data stores

- [ ] RDS PostgreSQL Multi-AZ (prod)
- [ ] Automated backups + tested restore
- [ ] ElastiCache not publicly reachable
- [ ] S3 buckets private; block public access
- [ ] Migrations applied (`scripts/migrate.py`) on empty and existing DBs

## 3. Compute & networking

- [ ] ECS services healthy (API, frontend, worker)
- [ ] Celery beat desired count = **1**
- [ ] ALB health checks on `/api/v1/health/live` and frontend `/`
- [ ] HTTPS via ACM; HTTP→HTTPS redirect
- [ ] Security groups least privilege
- [ ] CloudWatch log groups + retention set

## 4. Application hardening

- [ ] JWT required on all mutating business APIs (including ML writes)
- [ ] Rate limiting enabled
- [ ] HSTS enabled after HTTPS verified
- [ ] CSP tuned for SPA
- [ ] Admin/platform routes restricted to ADMIN/SUPER_ADMIN
- [ ] Default demo users disabled or passwords rotated

## 5. Observability

- [ ] Sentry DSN configured (or equivalent)
- [ ] `/metrics` scraped privately (not public)
- [ ] Alarms: 5xx, CPU, memory, RDS storage, Redis evictions
- [ ] Runbook link for on-call

## 6. Backups & DR

- [ ] Backup job verified (`/platform/backups/run` or infra snapshot)
- [ ] Restore drill documented
- [ ] RPO/RTO agreed (see archive DR doc)

## 7. CI/CD

- [ ] CI green on release tag
- [ ] Images tagged immutably (`v1.0.0`, git SHA)
- [ ] Production deploy requires approval
- [ ] Rollback procedure tested

## 8. Legal / ops

- [ ] LICENSE present
- [ ] Privacy / terms if SaaS customer-facing
- [ ] Support contact / security contact published

## Sign-off

| Role | Name | Date |
|------|------|------|
| Engineering | | |
| Security | | |
| Ops | | |
