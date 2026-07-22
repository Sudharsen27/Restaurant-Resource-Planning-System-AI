"""HTTP middleware: request/response logging, security headers, rate-limit, CSRF, HTTPS."""

from __future__ import annotations

import logging
import time
import uuid
from collections import defaultdict, deque
from threading import Lock

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response

from app.core.config import settings
from app.core.security import generate_csrf_token, security_headers

logger = logging.getLogger(__name__)

_SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}
_CSRF_EXEMPT_PREFIXES = (
    "/health",
    "/api/v1/health",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/metrics",
)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every API request and response with duration and status."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        start = time.perf_counter()
        client_ip = request.client.host if request.client else None
        # Propagate for downstream tracing
        request.state.request_id = request_id

        logger.info(
            "API request",
            extra={
                "event": "api_request",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": client_ip,
            },
        )

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.exception(
                "API request failed",
                extra={
                    "event": "api_exception",
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                    "client_ip": client_ip,
                },
            )
            raise

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        if settings.tracing_enabled:
            response.headers["X-Response-Time-Ms"] = str(duration_ms)

        logger.info(
            "API response",
            extra={
                "event": "api_response",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "client_ip": client_ip,
            },
        )
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach standard security headers when enabled via settings."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        response = await call_next(request)
        if settings.security_headers_enabled:
            for key, value in security_headers().items():
                response.headers.setdefault(key, value)
        return response


class HttpsRedirectMiddleware(BaseHTTPMiddleware):
    """Enforce HTTPS in production behind TLS-terminating proxies."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        if not settings.https_redirect_enabled:
            return await call_next(request)

        proto = request.headers.get("X-Forwarded-Proto", request.url.scheme)
        if proto != "https":
            url = request.url.replace(scheme="https")
            return RedirectResponse(str(url), status_code=308)
        return await call_next(request)


class CsrfProtectionMiddleware(BaseHTTPMiddleware):
    """Double-submit cookie CSRF for cookie-authenticated mutating requests.

    Bearer-token API clients are exempt (Authorization header present).
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        if not settings.csrf_enabled:
            return await call_next(request)

        path = request.url.path
        if any(path.startswith(p) for p in _CSRF_EXEMPT_PREFIXES):
            return await call_next(request)

        # Issue CSRF cookie on safe methods when missing
        if request.method in _SAFE_METHODS:
            response = await call_next(request)
            if settings.csrf_cookie_name not in request.cookies:
                token = generate_csrf_token()
                response.set_cookie(
                    settings.csrf_cookie_name,
                    token,
                    httponly=False,
                    samesite="lax",
                    secure=settings.is_production,
                    path="/",
                )
            return response

        # Mutating requests: skip if Authorization bearer present (SPA JWT)
        auth = request.headers.get("Authorization", "")
        if auth.lower().startswith("bearer "):
            return await call_next(request)

        cookie_token = request.cookies.get(settings.csrf_cookie_name)
        header_token = request.headers.get(settings.csrf_header_name)
        if not cookie_token or not header_token or cookie_token != header_token:
            return JSONResponse(
                status_code=403,
                content={
                    "success": False,
                    "message": "CSRF validation failed",
                    "detail": "CSRF validation failed",
                },
            )
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding-window rate limiter — Redis-backed when available, else memory."""

    def __init__(self, app) -> None:
        super().__init__(app)
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        if not settings.rate_limit_enabled:
            return await call_next(request)

        # Never throttle health/metrics
        if request.url.path.startswith("/health") or request.url.path.startswith("/metrics"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        window = settings.rate_limit_window_seconds
        limit = settings.rate_limit_requests

        allowed = True
        remaining = limit
        try:
            from app.services.cache_service import get_cache_service

            cache = get_cache_service()
            allowed, remaining = cache.rate_limit_hit(
                f"ip:{client_ip}",
                limit=limit,
                window_seconds=window,
            )
        except Exception:
            # Last-resort in-process limiter
            now = time.time()
            with self._lock:
                bucket = self._hits[client_ip]
                while bucket and bucket[0] <= now - window:
                    bucket.popleft()
                if len(bucket) >= limit:
                    allowed = False
                    remaining = 0
                else:
                    bucket.append(now)
                    remaining = limit - len(bucket)

        if not allowed:
            logger.warning(
                "Rate limit exceeded",
                extra={
                    "event": "rate_limit",
                    "client_ip": client_ip,
                    "path": request.url.path,
                },
            )
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "message": "Rate limit exceeded",
                    "errors": [],
                    "detail": "Rate limit exceeded",
                },
                headers={
                    "Retry-After": str(window),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
