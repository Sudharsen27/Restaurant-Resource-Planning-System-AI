# Security Review — v1.0.0

**Scope:** Static review of Backend auth, middleware, env handling, Docker, and CI. No application behavior changes were made as part of this review.

## Summary

| Area | Rating | Notes |
|------|--------|-------|
| Password hashing | Strong | bcrypt (direct), policy flags available |
| JWT / sessions | Good | Access + refresh, revoke APIs |
| CORS | Good | Allow-list via env |
| Rate limiting | Good | Redis-backed when enabled |
| Security headers | Good | Optional CSP/HSTS |
| Secrets hygiene | Mixed | Templates OK; compose defaults are dev-only |
| Route authorization | Gap | Some ML/legacy routes Public |
| Supply chain | Good | CI builds; pin major deps |

## Findings

### Secrets

- **Good:** `.env` gitignored; `env/*.env.example` has no live secrets.
- **Improve:** Ensure production never uses Compose default `SECRET_KEY`.
- **Improve:** Prefer IAM roles over static `AWS_ACCESS_KEY_ID` on ECS.
- **Improve:** Enable Secrets Manager rotation for RDS master password.

### JWT

- Implemented in `app/core/security.py` and `app/services/auth_service.py`.
- Sessions list/revoke endpoints exist.
- **Improve:** Short access TTL + refresh rotation audit in 1.1.
- **Improve:** Consider asymmetric keys (RS256) for multi-service verification later.

### CORS

- `CORSMiddleware` uses `settings.cors_origins_list`.
- **Improve:** Forbid `*` with credentials in production (validate at startup).

### Headers / HTTPS / CSRF

- `SecurityHeadersMiddleware`, `HttpsRedirectMiddleware`, `CsrfProtectionMiddleware`.
- Bearer JWT flows are CSRF-exempt (expected).
- **Improve:** Turn on HSTS only after HTTPS is confirmed end-to-end.

### Rate limiting

- `RateLimitMiddleware` + Redis.
- **Improve:** Separate limits for `/auth/login` vs authenticated APIs.

### Password hashing

- bcrypt via native library (passlib avoided due to bcrypt 5.x issues).
- Policy knobs: length, upper/lower/digit/special, lockout.

### Environment variables

- Stage-specific templates under `env/`.
- **Improve:** Fail fast if `APP_ENV=production` and `DEBUG=true` or weak `SECRET_KEY`.

### Open routes (priority)

ML/forecast/dataset/recommendation endpoints without JWT — documented for demos. **Must lock down before public internet exposure.**

### Docker / CI

- Non-root where feasible should be verified on Dockerfiles in 1.1.
- Deploy workflow secrets must remain GitHub encrypted secrets only.

## Recommended actions

| Priority | Action | Target |
|----------|--------|--------|
| P0 | Require JWT on ML/legacy write routes | 1.1.0 |
| P0 | Production startup guards for SECRET_KEY/DEBUG | 1.1.0 |
| P1 | Login-specific rate limits | 1.1.0 |
| P1 | Restrict `/metrics` at ALB | 1.1.0 |
| P2 | RS256 / key rotation | 2.0.0 |
| P2 | WAF + Shield | 2.0.0 |
