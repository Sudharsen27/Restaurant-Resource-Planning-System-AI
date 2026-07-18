"""HTTP middleware: request/response logging, security headers, rate-limit hook."""

from __future__ import annotations

import logging
import time
import uuid
from collections import defaultdict, deque
from threading import Lock

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import settings
from app.core.security import security_headers

logger = logging.getLogger(__name__)


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


class RateLimitMiddleware(BaseHTTPMiddleware):
    """In-memory sliding-window rate limiter (ready; off by default).

    Replace with Redis-backed limiter for multi-worker production.
    """

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

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window = settings.rate_limit_window_seconds
        limit = settings.rate_limit_requests

        with self._lock:
            bucket = self._hits[client_ip]
            while bucket and bucket[0] <= now - window:
                bucket.popleft()
            if len(bucket) >= limit:
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
                )
            bucket.append(now)

        return await call_next(request)
