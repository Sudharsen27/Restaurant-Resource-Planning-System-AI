# Deployment Topology

## Local / Compose

```mermaid
flowchart TB
  User[Browser :80] --> Nginx
  Nginx -->|/api| Backend
  Nginx -->|/| Frontend
  Backend --> Postgres
  Backend --> Redis
  Worker --> Redis
  Worker --> Postgres
  Scheduler --> Redis
```

## AWS target (v1.0 scaffolding → v1.1 complete)

```mermaid
flowchart TB
  Inet[Internet] --> ALB
  ALB -->|/| FE[ECS Frontend]
  ALB -->|/api| API[ECS API]
  API --> RDS[(RDS PostgreSQL)]
  API --> EC[(ElastiCache Redis)]
  API --> S3[(S3)]
  W[ECS Worker] --> EC
  W --> RDS
  W --> S3
  B[ECS Beat x1] --> EC
  SM[Secrets Manager] -.-> API
  SM -.-> W
  CW[CloudWatch Logs] <-.-> API
  CW <-.-> W
  ECR[ECR Images] -.-> API
  ECR -.-> FE
  ECR -.-> W
```

CDK lives in `infrastructure/` (`network`, `database`, `cache`, `compute` stacks). Full ECS service definitions and ALB rules are the primary **1.1.0** infra milestone.
