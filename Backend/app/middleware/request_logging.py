"""HTTP middleware: request/response logging, security headers, rate-limit, CSRF, HTTPS."""

from __future__ import annotations

import logging
import os
import time
import traceback
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


def _debug_middleware_enabled() -> bool:
    return bool(settings.debug) or str(settings.log_level).upper() == "DEBUG"


def _is_render_runtime() -> bool:
    """Render sets RENDER=true (and related vars) in the container environment."""
    return bool(os.getenv("RENDER")) or bool(os.getenv("RENDER_SERVICE_ID"))


def _behind_tls_terminating_proxy(request: Request) -> bool:
    """True when a reverse proxy already handles TLS (Render, ALB, nginx, etc.)."""
    if _is_render_runtime():
        return True
    # Any X-Forwarded-Proto means we are behind a proxy — do not app-level redirect.
    return "x-forwarded-proto" in {k.lower() for k in request.headers.keys()}


def _mw_log(name: str, request: Request, phase: str, exc: BaseException | None = None) -> None:
    if not _debug_middleware_enabled():
        return
    msg = f"[mw] {name} {phase} path={request.url.path} method={request.method}"
    if exc is not None:
        logger.error("%s error=%s\n%s", msg, exc, traceback.format_exc())
    else:
        logger.debug(msg)


def _safe_error_response(exc: BaseException) -> JSONResponse:
    """Return a JSON 500 instead of dropping the connection (which becomes a proxy 502)."""
    logger.exception("Middleware pipeline failure: %s", exc)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "An unexpected error occurred",
            "errors": [],
            "detail": "An unexpected error occurred",
        },
    )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every API request and response with duration and status."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        _mw_log("RequestLogging", request, "entered")
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        start = time.perf_counter()
        client_ip = request.client.host if request.client else None
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
        except Exception as exc:
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
            _mw_log("RequestLogging", request, "exception", exc)
            return _safe_error_response(exc)

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
        _mw_log("RequestLogging", request, "exited")
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach standard security headers when enabled via settings.

    Docs endpoints (/docs, /redoc, /openapi.json) receive a scoped CSP that
    allows Swagger UI CDN assets; API routes keep the strict global CSP.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        _mw_log("SecurityHeaders", request, "entered")
        try:
            response = await call_next(request)
            if settings.security_headers_enabled:
                for key, value in security_headers(path=request.url.path).items():
                    # Docs need their CSP to win over any prior default.
                    if key == "Content-Security-Policy" and request.url.path.startswith(
                        ("/docs", "/redoc", "/openapi.json")
                    ):
                        response.headers[key] = value
                    else:
                        response.headers.setdefault(key, value)
            _mw_log("SecurityHeaders", request, "exited")
            return response
        except Exception as exc:
            _mw_log("SecurityHeaders", request, "exception", exc)
            return _safe_error_response(exc)


class HttpsRedirectMiddleware(BaseHTTPMiddleware):
    """Enforce HTTPS when enabled — but never behind Render / TLS-terminating proxies.

    AWS ALB / Render terminate TLS and forward HTTP to the container with
    ``X-Forwarded-Proto``. App-level redirects in that path cause proxy failures
    (often surfaced as 502 Bad Gateway). Direct non-proxy access can still redirect.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        _mw_log("HttpsRedirect", request, "entered")
        try:
            if not settings.https_redirect_enabled:
                response = await call_next(request)
                _mw_log("HttpsRedirect", request, "exited")
                return response

            # Render / proxy: TLS is handled at the edge — do not 308 inside the app.
            if _behind_tls_terminating_proxy(request):
                if _debug_middleware_enabled():
                    logger.debug(
                        "HttpsRedirect skipped (proxy/Render) path=%s xfp=%s render=%s",
                        request.url.path,
                        request.headers.get("X-Forwarded-Proto"),
                        _is_render_runtime(),
                    )
                response = await call_next(request)
                _mw_log("HttpsRedirect", request, "exited")
                return response

            proto = request.headers.get("X-Forwarded-Proto", request.url.scheme)
            if str(proto).split(",")[0].strip().lower() != "https":
                url = request.url.replace(scheme="https")
                _mw_log("HttpsRedirect", request, "exited-redirect")
                return RedirectResponse(str(url), status_code=308)

            response = await call_next(request)
            _mw_log("HttpsRedirect", request, "exited")
            return response
        except Exception as exc:
            _mw_log("HttpsRedirect", request, "exception", exc)
            return _safe_error_response(exc)


class CsrfProtectionMiddleware(BaseHTTPMiddleware):
    """Double-submit cookie CSRF for cookie-authenticated mutating requests.

    Bearer-token API clients are exempt (Authorization header present).
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        _mw_log("CsrfProtection", request, "entered")
        try:
            if not settings.csrf_enabled:
                response = await call_next(request)
                _mw_log("CsrfProtection", request, "exited")
                return response

            path = request.url.path
            if any(path.startswith(p) for p in _CSRF_EXEMPT_PREFIXES):
                response = await call_next(request)
                _mw_log("CsrfProtection", request, "exited")
                return response

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
                _mw_log("CsrfProtection", request, "exited")
                return response

            auth = request.headers.get("Authorization", "")
            if auth.lower().startswith("bearer "):
                response = await call_next(request)
                _mw_log("CsrfProtection", request, "exited")
                return response

            cookie_token = request.cookies.get(settings.csrf_cookie_name)
            header_token = request.headers.get(settings.csrf_header_name)
            if not cookie_token or not header_token or cookie_token != header_token:
                _mw_log("CsrfProtection", request, "exited-403")
                return JSONResponse(
                    status_code=403,
                    content={
                        "success": False,
                        "message": "CSRF validation failed",
                        "detail": "CSRF validation failed",
                    },
                )
            response = await call_next(request)
            _mw_log("CsrfProtection", request, "exited")
            return response
        except Exception as exc:
            _mw_log("CsrfProtection", request, "exception", exc)
            return _safe_error_response(exc)


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
        _mw_log("RateLimit", request, "entered")
        try:
            if not settings.rate_limit_enabled:
                response = await call_next(request)
                _mw_log("RateLimit", request, "exited")
                return response

            if request.url.path.startswith("/health") or request.url.path.startswith("/metrics"):
                response = await call_next(request)
                _mw_log("RateLimit", request, "exited")
                return response

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
                _mw_log("RateLimit", request, "exited-429")
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
            _mw_log("RateLimit", request, "exited")
            return response
        except Exception as exc:
            _mw_log("RateLimit", request, "exception", exc)
            return _safe_error_response(exc)
