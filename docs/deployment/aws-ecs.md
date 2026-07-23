# Deploy on AWS ECS Fargate

Target architecture: **ECR → ECS Fargate → ALB → RDS + ElastiCache + S3 + Secrets Manager + CloudWatch**.

## 1. Container images (ECR)

Create repositories:

- `rrps-backend`
- `rrps-worker` (or reuse backend worker tag)
- `rrps-frontend`

Build and push (example):

```bash
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com

docker build -t rrps-backend ./Backend
docker tag rrps-backend:latest $ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com/rrps-backend:v1.0.0
docker push $ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com/rrps-backend:v1.0.0

docker build -f Backend/Dockerfile.worker -t rrps-worker ./Backend
docker build -t rrps-frontend ./Frontend
# tag + push similarly
```

## 2. Networking

- VPC with public + private subnets (see CDK `infrastructure/lib/network-stack.ts`)
- ALB in public subnets
- ECS tasks, RDS, ElastiCache in private subnets
- Security groups: ALB → API:8000 / Frontend:80; API/Worker → RDS:5432 + Redis:6379

## 3. ECS services

| Service | Desired count | Notes |
|---------|---------------|-------|
| `api` | 2+ | Health check `/api/v1/health/live` |
| `frontend` | 2+ | Serves static nginx |
| `worker` | 1+ | Celery concurrency sized to CPU |
| `beat` | **1** | Exactly one scheduler |
| `migrate` | one-off task | Run before each release |

### ALB listener rules

| Path | Target |
|------|--------|
| `/api/*` | API target group `:8000` |
| `/metrics` | API (restrict by SG / auth in future) |
| `/*` | Frontend `:80` |

## 4. Task definition essentials

- **CPU/Memory:** start `512/1024` API; tune workers separately
- **Log driver:** `awslogs` → CloudWatch log groups
- **Secrets:** inject from Secrets Manager / SSM (`DATABASE_URL`, `SECRET_KEY`, Redis URLs)
- **IAM task role:** S3 read/write; no long-lived AWS keys in env when possible
- **Environment:** `APP_ENV=production`, `LOG_FORMAT=json`, `STORAGE_BACKEND=s3`

## 5. Deploy flow

1. `cdk deploy` network + database + cache (+ compute when ready)
2. Push images to ECR
3. Run migrate task
4. Update ECS services (rolling)
5. Verify `/health/ready`, login, place test order

## 6. CDK status (v1.0)

`infrastructure/` contains network, database (RDS), cache (ElastiCache), and compute scaffolding. Completing ECS task definitions, ALB wiring, and CI→ECR→ECS is the primary **1.1.0** infra deliverable.

## GitHub Actions

`.github/workflows/deploy.yml` currently targets GHCR + webhook. Point it at ECR + `aws ecs update-service` when AWS credentials are configured.
