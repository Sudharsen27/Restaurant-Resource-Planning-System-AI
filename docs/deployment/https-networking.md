# HTTPS & Networking

## Local Compose

Nginx terminates HTTP on port 80 and routes:

| Path | Upstream |
|------|----------|
| `/api/` | `backend:8000` |
| `/` | `frontend:80` |

For local HTTPS, put Caddy/Traefik or mkcert in front of Compose, or use a tunnel.

## AWS

1. Request / import ACM certificate for your domain.
2. ALB HTTPS listener `:443` with cert; redirect `:80` → `:443`.
3. Set `HTTPS_REDIRECT_ENABLED=true` so the API trusts `X-Forwarded-Proto`.
4. Set `HSTS_ENABLED=true` after HTTPS is stable.
5. Restrict `CORS_ORIGINS` to the real SPA origin(s), e.g. `https://app.example.com`.

## Security headers

Enabled via middleware when `SECURITY_HEADERS_ENABLED=true`:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- Referrer-Policy
- Optional CSP / HSTS

## Rate limiting

`RATE_LIMIT_ENABLED=true` with Redis stores sliding counters. Tune `RATE_LIMIT_REQUESTS` / `RATE_LIMIT_WINDOW_SECONDS` per environment.

## Network hardening checklist

- [ ] No public RDS / Redis
- [ ] ALB-only public ingress
- [ ] Security groups least privilege
- [ ] CloudWatch alarms on 5xx / unhealthy hosts
- [ ] WAF (optional) on ALB for public apps
