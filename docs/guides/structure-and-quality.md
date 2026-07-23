# Structure & quality notes (v1.0 polish)

Non-behavioral review notes for maintainers.

## Repository structure

| Finding | Recommendation | Status |
|---------|----------------|--------|
| Dual `infra/` vs `infrastructure/` | Document clearly in README | Done |
| Phase reports cluttering `docs/` | Archive under `docs/archive/phase-reports/` | Done |
| Missing LICENSE / CONTRIBUTING / CHANGELOG | Add MIT + community files | Done |
| Frontend package `0.0.0` | Bump to `1.0.0` | Done |
| `scripts/` for tooling | Endpoint index generator added | Done |
| Orphan `Backend/app/api/feedback.py` | Confirm unused → remove in 1.1 | Deferred |
| Local `verify_*.db` | Keep gitignored | OK |

## Backend quality

| Finding | Recommendation |
|---------|----------------|
| Dual mount `/api/v1` + `/` | Prefer documenting `/api/v1` only; deprecate legacy in 1.1 |
| Large router modules (`catalog`, `crm_hrms`) | Optional split by subdomain later — no behavior change now |
| `passlib` still in requirements while using bcrypt directly | Remove unused dep in 1.1 after confirming |
| ML routes public | Security hardening 1.1 |

## Frontend quality

| Finding | Recommendation |
|---------|----------------|
| Lint clean after hooks refactor | Keep CI gate |
| No E2E | Playwright smoke in 1.1 |
| Large page modules | Acceptable for v1; code-split already via lazy routes |

## Docker / CI

| Finding | Recommendation |
|---------|----------------|
| Compose healthy for local prod-like | Keep as golden path |
| Deploy → GHCR | Migrate to ECR in 1.1 |
| Ruff non-blocking in CI | Optionally enforce select rules later |

## Performance (no code changes)

- Enable Redis cache for hot GET dashboards in prod
- Size Celery concurrency to vCPU
- Prefer S3 for uploads (avoid shared EFS unless required)
- ALB stickiness not required for stateless API
