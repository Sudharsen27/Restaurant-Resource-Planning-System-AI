"""Security utilities — JWT helpers and response security headers."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.config import settings
from app.core.exceptions import UnauthorizedError


def create_access_token(
    subject: str,
    *,
    expires_minutes: int | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Create a JWT access token.

    Requires PyJWT (`pip install PyJWT`) when auth is enabled.
    Until then, this raises to avoid silent insecure tokens.
    """
    try:
        import jwt
    except ImportError as exc:
        raise RuntimeError(
            "PyJWT is required for JWT auth. Add PyJWT to requirements.txt."
        ) from exc

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.jwt_expire_minutes
    )
    payload: dict[str, Any] = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(
        payload,
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT access token."""
    try:
        import jwt
    except ImportError as exc:
        raise RuntimeError(
            "PyJWT is required for JWT auth. Add PyJWT to requirements.txt."
        ) from exc

    try:
        return jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("Invalid or expired token") from exc


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def security_headers() -> dict[str, str]:
    """Standard security headers for responses (CSP / HSTS optional)."""
    headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "X-XSS-Protection": "1; mode=block",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    }
    csp = settings.effective_csp
    if csp:
        headers["Content-Security-Policy"] = csp
    if settings.hsts_enabled or (settings.is_production and settings.https_redirect_enabled):
        headers["Strict-Transport-Security"] = (
            f"max-age={settings.hsts_max_age_seconds}; includeSubDomains; preload"
        )
    return headers
