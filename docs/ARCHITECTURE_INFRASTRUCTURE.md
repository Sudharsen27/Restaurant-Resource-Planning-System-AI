# Architecture & Infrastructure Diagrams

## Application architecture

```mermaid
flowchart TB
  subgraph Edge
    NGX[Nginx TLS / gzip / rate limit]
  end
  subgraph Apps
    FE[React SPA]
    API[FastAPI API]
    W[Celery Worker]
    B[Celery Beat]
  end
  subgraph Data
    PG[(PostgreSQL)]
    RD[(Redis)]
    OBJ[(Object Storage)]
  end
  Clients --> NGX
  NGX --> FE
  NGX --> API
  API --> PG
  API --> RD
  API --> OBJ
  W --> PG
  W --> RD
  W --> OBJ
  B --> RD
  RD --> W
```

## Multi-cloud deployment pattern

```mermaid
flowchart LR
  subgraph Control
    GH[GitHub Actions]
    REG[Container Registry]
  end
  subgraph Runtime
    ORCH[ECS / AKS / GKE / DO / Compose]
    API2[API replicas]
    WK[Workers]
    SCH[Scheduler]
  end
  subgraph Managed
    DB[(Managed Postgres)]
    CACHE[(Managed Redis)]
    STORE[(S3 / Blob / GCS / R2)]
  end
  GH --> REG --> ORCH
  ORCH --> API2
  ORCH --> WK
  ORCH --> SCH
  API2 --> DB
  API2 --> CACHE
  API2 --> STORE
  WK --> DB
  WK --> CACHE
```

## Security layers

1. Edge TLS + CSP/HSTS headers (Nginx + FastAPI middleware)
2. JWT access + rotating refresh tokens
3. Optional CSRF for cookie flows; bearer SPA exempt
4. Redis rate limiting
5. RBAC on platform ops endpoints
6. Secrets outside git
