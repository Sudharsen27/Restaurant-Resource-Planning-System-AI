# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2026-07-23

### Added

- Full Restaurant ERP SaaS platform (MDM, catalog, inventory, POS, CRM/HRMS, BI, admin, multi-tenant SaaS)
- FastAPI backend with PostgreSQL, Redis, Celery worker/beat
- React 19 + Vite SPA with Platform Ops and SaaS consoles
- Docker Compose stack (postgres, redis, backend, worker, scheduler, frontend, nginx)
- GitHub Actions CI (backend tests, frontend lint/build, Docker image builds)
- Deploy workflow skeleton (GHCR push, migrate, webhook)
- Health/readiness endpoints, Prometheus `/metrics`, JSON logging
- Storage abstraction (local / S3 / R2 / Azure / GCS)
- AWS CDK scaffolding under `infrastructure/` (network, database, cache, compute)
- Environment templates for development, testing, staging, and production

### Security

- JWT access/refresh tokens, session revocation
- bcrypt password hashing, password policy settings
- CORS, CSRF (cookie), rate limiting, security headers, optional HSTS/HTTPS redirect

### Documentation

- Enterprise README, architecture diagrams, API reference, deployment guides
- Production checklist and security review

## [Unreleased]

### Planned (1.1.0)

- Harden remaining public ML/legacy routes behind JWT where appropriate
- Complete AWS CDK ECS/ALB task definitions and ECR deploy path
- Expand automated API integration test coverage
- Frontend E2E smoke tests

[1.0.0]: https://github.com/Sudharsen27/Restaurant-Resource-Planning-System-AI/releases/tag/v1.0.0
