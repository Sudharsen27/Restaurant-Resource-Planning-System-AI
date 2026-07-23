# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | Yes       |
| < 1.0   | No        |

## Reporting a vulnerability

Please report security issues privately.

1. Email the repository maintainers, **or**
2. Use GitHub **Security Advisories** on this repository (preferred if available).

Include:

- Description of the issue
- Steps to reproduce
- Affected component (API route, auth, Docker, CI, etc.)
- Impact assessment (auth bypass, data exposure, RCE, etc.)

We will acknowledge reports as soon as practical and coordinate a fix and disclosure timeline.

## Do not

- Open public GitHub issues for vulnerabilities
- Commit secrets, production credentials, or private keys
- Share exploit PoCs publicly before a fix is released

## Security baseline (v1.0.0)

- JWT authentication with refresh tokens and session revocation
- bcrypt password hashing
- Configurable CORS allow-list
- Rate limiting (Redis-backed when enabled)
- Security headers (CSP/HSTS optional)
- CSRF protection for cookie-based flows (Bearer JWT exempt)
- Secrets expected from environment / Secrets Manager in production

See [docs/security/SECURITY_REVIEW.md](docs/security/SECURITY_REVIEW.md) for the full audit notes.
