"""Health endpoint and HealthService unit tests."""

from app.services.health_service import HealthService


def test_liveness_payload():
    payload = HealthService().liveness()
    assert payload["status"] == "ok"
    assert payload["check"] == "live"
    assert "timestamp" in payload


def test_resources_report_shape():
    resources = HealthService()._resources()
    assert "ok" in resources
    if resources["ok"]:
        assert "cpu_percent" in resources
        assert "memory" in resources
        assert "disk" in resources


def test_readiness_shape():
    payload = HealthService().readiness()
    assert payload["check"] == "ready"
    assert "checks" in payload
    assert "database" in payload["checks"]
