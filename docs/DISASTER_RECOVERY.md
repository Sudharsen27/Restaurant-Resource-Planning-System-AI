# Disaster Recovery Plan

## Objectives

| Metric | Target |
|--------|--------|
| RPO (data loss) | ≤ 24h (daily backups); ≤ 1h with continuous WAL archiving |
| RTO (restore time) | ≤ 4h for full DB restore on staging-sized data |

## Backup strategy

1. **Automated dumps** — `Backend/scripts/backup_postgres.sh` (or `/platform/backups/run` for SUPER_ADMIN)
2. **Retention** — `BACKUP_RETENTION_DAYS` (7/14/30 by env)
3. **Verification** — `verify_backup.sh` (size + gzip test + checksum)
4. **Offsite** — copy `backups/` to S3/Azure/GCS daily (cron/CI)

## Restore process

1. Stop writers (scale API/worker to 0) or use maintenance mode.
2. Provision empty database (or restore into new instance).
3. `./scripts/restore_postgres.sh /path/to/rrps_*.sql.gz`
4. Run `alembic upgrade head` if dump is older than code.
5. Start API → verify `/health/ready`.
6. Start workers/scheduler.
7. Spot-check auth login, POS, inventory counts.

## Failure scenarios

| Scenario | Response |
|----------|----------|
| Single API pod crash | Orchestrator restarts; no data loss |
| Redis outage | Cache/rate-limit fall back to memory; queues pause until Redis restored |
| Worker crash | Celery acks_late + retries redeliver jobs |
| DB primary loss | Promote replica / restore from backup |
| Bad deploy | Roll image to previous SHA; avoid irreversible migrations |

## Storage verification

- After each backup: `scripts/verify_backup.sh <file>`
- Weekly: restore to a throwaway database and run smoke tests
- Confirm object storage (`/platform/storage`) health for uploads

## Contacts / ownership

Document on-call rotation and escalation in your ops runbook (PagerDuty/Opsgenie). This repo provides the technical restore path; staffing is environment-specific.
