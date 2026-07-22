"""Prometheus metrics endpoint and request counters."""

from __future__ import annotations

from fastapi import APIRouter, Response

from app.core.config import settings

router = APIRouter(tags=["metrics"])

_REQUEST_COUNT = 0
_ERROR_COUNT = 0


def record_request(*, is_error: bool = False) -> None:
    global _REQUEST_COUNT, _ERROR_COUNT
    _REQUEST_COUNT += 1
    if is_error:
        _ERROR_COUNT += 1


@router.get("/metrics")
def metrics() -> Response:
    if not settings.metrics_enabled:
        return Response(content="metrics disabled\n", media_type="text/plain", status_code=404)

    try:
        from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Gauge, generate_latest

        registry = CollectorRegistry()
        g_req = Gauge("rrps_requests_total", "Process request counter", registry=registry)
        g_err = Gauge("rrps_errors_total", "Process error counter", registry=registry)
        g_req.set(_REQUEST_COUNT)
        g_err.set(_ERROR_COUNT)

        from app.services.health_service import get_health_service

        resources = get_health_service()._resources()
        if resources.get("ok"):
            Gauge("rrps_cpu_percent", "CPU percent", registry=registry).set(
                float(resources.get("cpu_percent") or 0)
            )
            Gauge("rrps_memory_percent", "Memory percent", registry=registry).set(
                float((resources.get("memory") or {}).get("percent") or 0)
            )
            Gauge("rrps_disk_percent", "Disk percent", registry=registry).set(
                float((resources.get("disk") or {}).get("percent") or 0)
            )

        return Response(content=generate_latest(registry), media_type=CONTENT_TYPE_LATEST)
    except Exception as exc:
        body = (
            f"# metrics fallback\n"
            f"rrps_requests_total {_REQUEST_COUNT}\n"
            f"rrps_errors_total {_ERROR_COUNT}\n"
            f"# error {exc}\n"
        )
        return Response(content=body, media_type="text/plain")
