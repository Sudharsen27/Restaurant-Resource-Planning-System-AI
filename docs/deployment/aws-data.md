# AWS RDS & ElastiCache

## RDS PostgreSQL

| Setting | Recommendation |
|---------|----------------|
| Engine | PostgreSQL 16 |
| Placement | Private subnets |
| Multi-AZ | Yes for production |
| Storage | gp3, enable autoscaling |
| Backups | 7–35 day retention |
| Credentials | Secrets Manager rotation |
| Connectivity | From ECS SG only |

**App config**

```env
DATABASE_URL=postgresql://USER:PASSWORD@RDS_ENDPOINT:5432/restaurant_rps
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_STATEMENT_TIMEOUT_SECONDS=30
```

Run migrations as a one-off Fargate task:

```bash
python scripts/migrate.py
```

## ElastiCache Redis

| Setting | Recommendation |
|---------|----------------|
| Engine | Redis 7 |
| Mode | Cluster optional; start with single primary + replica |
| Encryption | In-transit + at-rest |
| Auth token | Enabled |
| Placement | Private subnets |

**App config**

```env
REDIS_URL=rediss://:TOKEN@REDIS_ENDPOINT:6379/0
CELERY_BROKER_URL=rediss://:TOKEN@REDIS_ENDPOINT:6379/1
CELERY_RESULT_BACKEND=rediss://:TOKEN@REDIS_ENDPOINT:6379/2
REDIS_ENABLED=true
```

Logical DB separation (0 cache, 1 broker, 2 results) matches Compose defaults.

## S3

```env
STORAGE_BACKEND=s3
S3_BUCKET=rrps-prod-assets
AWS_REGION=ap-south-1
# Prefer IAM task role — leave access keys empty
```

CDK references: `infrastructure/lib/database-stack.ts`, `infrastructure/lib/cache-stack.ts`.
