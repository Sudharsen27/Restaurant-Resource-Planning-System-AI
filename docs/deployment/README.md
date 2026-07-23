# Deployment Documentation

| Guide | Topic |
|-------|-------|
| [Docker Compose](docker-compose.md) | Local / single-host production-like stack |
| [AWS ECS](aws-ecs.md) | Fargate services, ECR, ALB |
| [RDS & Redis](aws-data.md) | PostgreSQL RDS + ElastiCache |
| [Environment variables](environment-variables.md) | Required secrets and config |
| [HTTPS & networking](https-networking.md) | TLS, CORS, security headers |

CDK scaffolding: `infrastructure/` (network, database, cache, compute).
