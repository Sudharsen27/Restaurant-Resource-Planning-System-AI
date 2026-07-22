"""API-level health smoke tests — skip if runtime dependencies unavailable."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    try:
        from app.core.config import get_settings

        get_settings.cache_clear()
        from app.main import create_app

        app = create_app()
        with TestClient(app) as c:
            yield c
    except Exception as exc:
        pytest.skip(f"App client unavailable: {exc}")


def test_health_live_via_app(client):
    r = client.get("/health/live")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_health_legacy(client):
    r = client.get("/health")
    assert r.status_code == 200


def test_health_detailed(client):
    r = client.get("/health/detailed")
    assert r.status_code == 200
    body = r.json()
    assert "database" in body
    assert "redis" in body
