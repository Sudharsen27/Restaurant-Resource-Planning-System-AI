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


# FastAPI docs UIs load Swagger/ReDoc assets from jsDelivr; keep this CSP scoped to docs only.
_DOCS_PATH_PREFIXES = ("/docs", "/redoc", "/openapi.json")

_DOCS_CSP = (
    "default-src 'self'; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "img-src 'self' data:; "
    "font-src 'self' https://cdn.jsdelivr.net; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self'"
)


def _is_docs_path(path: str) -> bool:
    return (
        path == "/openapi.json"
        or path.startswith("/docs")
        or path.startswith("/redoc")
    )


def security_headers(path: str | None = None) -> dict[str, str]:
    """Standard security headers for responses (CSP / HSTS optional).

    When ``path`` is a FastAPI docs endpoint (/docs, /redoc, /openapi.json),
    apply a docs-only CSP that allows Swagger UI CDN assets. All other routes
    keep the strict global CSP from settings.
    """
    headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "X-XSS-Protection": "1; mode=block",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    }
    if path and _is_docs_path(path):
        if settings.csp_enabled:
            headers["Content-Security-Policy"] = _DOCS_CSP
    else:
        csp = settings.effective_csp
        if csp:
            headers["Content-Security-Policy"] = csp
    if settings.hsts_enabled or (settings.is_production and settings.https_redirect_enabled):
        headers["Strict-Transport-Security"] = (
            f"max-age={settings.hsts_max_age_seconds}; includeSubDomains; preload"
        )
    return headers
