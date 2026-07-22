"""Shared pytest fixtures for Phase 12 infrastructure tests."""

from __future__ import annotations

import os

import pytest

# Ensure test-friendly defaults before app imports
os.environ.setdefault("APP_ENV", "testing")
os.environ.setdefault("CELERY_TASK_ALWAYS_EAGER", "true")
os.environ.setdefault("REDIS_ENABLED", "false")
os.environ.setdefault("METRICS_ENABLED", "false")
os.environ.setdefault("SEED_ENTERPRISE_DATA", "false")
os.environ.setdefault("SEED_LEGACY_FORECASTS", "false")
os.environ.setdefault("ALLOW_CREATE_ALL", "true")
os.environ.setdefault("SECRET_KEY", "test-secret-key-phase12-32chars!!")


@pytest.fixture(scope="session")
def any_settings():
    from app.core.config import get_settings

    get_settings.cache_clear()
    return get_settings()


@pytest.fixture
def cache_service(monkeypatch):
    monkeypatch.setenv("REDIS_ENABLED", "false")
    from app.core.config import get_settings
    from app.services import cache_service as cs

    get_settings.cache_clear()
    cs._cache_service = None
    service = cs.get_cache_service()
    yield service
    cs._cache_service = None
    get_settings.cache_clear()


@pytest.fixture
def storage_service(tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    monkeypatch.setenv("STORAGE_LOCAL_ROOT", str(tmp_path))
    from app.core.config import get_settings
    from app.services import storage_service as ss

    get_settings.cache_clear()
    ss._storage_service = None
    service = ss.get_storage_service()
    yield service
    ss._storage_service = None
    get_settings.cache_clear()
