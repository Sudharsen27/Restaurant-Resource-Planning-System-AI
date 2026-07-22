# CI/CD Guide

## Workflows

### `CI` (`.github/workflows/ci.yml`)

On push/PR:

1. **Backend** — install, ruff (soft), compileall, Alembic upgrade, pytest (Postgres + Redis services)
2. **Frontend** — npm install, lint, production build
3. **Docker** — build backend, worker, frontend images (no push)

### `Deploy` (`.github/workflows/deploy.yml`)

On version tags `v*` or manual `workflow_dispatch`:

1. Build & push images to GHCR
2. Run Alembic `upgrade head` against `secrets.DATABASE_URL`
3. Call `secrets.DEPLOY_WEBHOOK_URL` for orchestrator rolling update

## Required GitHub secrets / variables

| Secret | Purpose |
|--------|---------|
| `DATABASE_URL` | Migration + runtime DB |
| `SECRET_KEY` | JWT signing |
| `DEPLOY_WEBHOOK_URL` | Optional deploy hook (ECS/K8s/DO) |
| `GITHUB_TOKEN` | GHCR push (provided) |

Use GitHub **Environments** (`staging`, `production`) with protection rules.

## Pipeline principles

- Never commit secrets
- Migrations run **before** traffic shift when additive; follow expand/contract for breaking changes
- Images tagged by git SHA for immutable rollbacks
- Workers restart after API health checks pass
