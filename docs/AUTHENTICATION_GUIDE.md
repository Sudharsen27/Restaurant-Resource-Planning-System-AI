# Authentication Guide (Production)

## Flows

1. **Register / Login** → access JWT + refresh JWT + session row
2. **Refresh** → rotates refresh token (old hash invalidated)
3. **Logout** → revokes session
4. **Password change/reset** → strength policy + history

## Password policy

Configurable via env:

- Minimum length (`PASSWORD_MIN_LENGTH`, prod recommend ≥ 12)
- Upper, lower, digit, special required

## Tokens

| Token | TTL (typical) | Storage |
|-------|---------------|---------|
| Access | 15–30 min | Client memory / auth header |
| Refresh | 7–14 days | Hashed in DB; rotated on use |

Send `Authorization: Bearer <access>`.

## Hardening toggles

| Feature | Env | Notes |
|---------|-----|-------|
| Security headers + CSP | `SECURITY_HEADERS_ENABLED`, `CSP_ENABLED` | Default on |
| HSTS | `HSTS_ENABLED` | Enable with HTTPS |
| HTTPS redirect | `HTTPS_REDIRECT_ENABLED` | Trust `X-Forwarded-Proto` |
| CSRF | `CSRF_ENABLED` | Cookie+header; bearer clients exempt |
| Rate limit | `RATE_LIMIT_ENABLED` | Redis-backed when available |
| Account lockout | `MAX_FAILED_LOGIN_ATTEMPTS` | Existing auth service |

## Production checklist

- [ ] Unique `SECRET_KEY` from secrets manager
- [ ] HTTPS at edge
- [ ] `APP_ENV=production`, `DEBUG=false`
- [ ] Rate limiting on
- [ ] Short access token TTL
- [ ] CORS limited to real origins
