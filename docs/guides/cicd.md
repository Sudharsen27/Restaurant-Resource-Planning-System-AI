# CI/CD Guide

## Workflows

### `ci.yml` — continuous integration

**Triggers:** push/PR to `main`, `master`, `develop`, `phase-*`

| Job | Steps |
|-----|-------|
| Backend | Install deps → ruff (advisory) → compileall → migrate → pytest |
| Frontend | `npm ci` → lint → build |
| Docker | buildx build backend / worker / frontend (no push) |

### `deploy.yml` — release

**Triggers:** `workflow_dispatch` or tag `v*`

| Step | Behavior |
|------|----------|
| Build & push | GHCR images |
| Migrate | Uses secrets / remote migrate hook |
| Deploy | Webhook curl to environment |

## Required GitHub secrets (deploy)

Configure as needed: registry credentials, `DATABASE_URL`, deploy webhook URL, cloud keys.

## Promoting v1.0.0

```bash
git tag v1.0.0
git push origin v1.0.0
```

## Next (1.1.0)

- Push to **ECR**
- `aws ecs update-service --force-new-deployment`
- Environment protection rules for production
