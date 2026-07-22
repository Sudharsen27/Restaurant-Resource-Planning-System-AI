"""Cache service tests (in-memory backend)."""


def test_cache_set_get_delete(cache_service):
    cache_service.cache_set("k1", {"a": 1}, ttl=60)
    assert cache_service.cache_get("k1") == {"a": 1}
    cache_service.delete("cache", "k1")
    assert cache_service.cache_get("k1") is None


def test_session_namespace(cache_service):
    cache_service.session_set("sess-1", {"user_id": 7}, ttl=120)
    assert cache_service.session_get("sess-1")["user_id"] == 7
    cache_service.session_delete("sess-1")
    assert cache_service.session_get("sess-1") is None


def test_rate_limit_window(cache_service):
    allowed, remaining = cache_service.rate_limit_hit("ip:test", limit=3, window_seconds=60)
    assert allowed is True
    assert remaining == 2
    cache_service.rate_limit_hit("ip:test", limit=3, window_seconds=60)
    allowed, remaining = cache_service.rate_limit_hit("ip:test", limit=3, window_seconds=60)
    assert allowed is True
    allowed, remaining = cache_service.rate_limit_hit("ip:test", limit=3, window_seconds=60)
    assert allowed is False
    assert remaining == 0


def test_clear_namespace(cache_service):
    cache_service.set("cache", "a", 1)
    cache_service.set("cache", "b", 2)
    deleted = cache_service.clear_namespace("cache")
    assert deleted >= 2
