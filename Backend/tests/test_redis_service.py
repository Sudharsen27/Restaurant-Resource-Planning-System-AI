from __future__ import annotations

from app.services.redis_service import RedisService


class FakeRedisClient:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.last_ttl: int | None = None
        self.fail = False

    def get(self, name: str) -> str | None:
        if self.fail:
            raise ConnectionError("Redis unavailable")
        return self.values.get(name)

    def set(self, name: str, value: str, ex: int | None = None) -> bool:
        if self.fail:
            raise ConnectionError("Redis unavailable")
        self.values[name] = value
        self.last_ttl = ex
        return True

    def delete(self, *names: str) -> int:
        if self.fail:
            raise ConnectionError("Redis unavailable")
        deleted = 0
        for name in names:
            if name in self.values:
                del self.values[name]
                deleted += 1
        return deleted

    def exists(self, *names: str) -> int:
        if self.fail:
            raise ConnectionError("Redis unavailable")
        return sum(name in self.values for name in names)

    def ping(self) -> bool:
        if self.fail:
            raise ConnectionError("Redis unavailable")
        return True


def test_redis_service_serializes_json_with_prefix_and_ttl():
    client = FakeRedisClient()
    service = RedisService(client, key_prefix="rrps")

    assert service.set_json("catalog:products", {"id": "p-1"}, ttl_seconds=300)
    assert client.last_ttl == 300
    assert service.get_json("catalog:products") == {"id": "p-1"}
    assert service.exists("catalog:products")


def test_redis_service_deletes_keys():
    client = FakeRedisClient()
    service = RedisService(client, key_prefix="rrps")
    service.set_json("catalog:products", ["p-1"])

    assert service.delete("catalog:products")
    assert not service.exists("catalog:products")


def test_redis_service_fails_open_when_redis_is_unavailable():
    client = FakeRedisClient()
    service = RedisService(client, key_prefix="rrps")
    client.fail = True

    assert service.get_json("catalog:products") is None
    assert not service.set_json("catalog:products", {"id": "p-1"})
    assert not service.delete("catalog:products")
    assert not service.exists("catalog:products")
    assert not service.ping()


def test_redis_service_validates_keys_and_ttl():
    service = RedisService(FakeRedisClient(), key_prefix="rrps")

    try:
        service.set_json("catalog:products", {"id": "p-1"}, ttl_seconds=0)
    except ValueError as exc:
        assert str(exc) == "ttl_seconds must be greater than zero"
    else:
        raise AssertionError("Expected TTL validation error")

    try:
        service.get_json("")
    except ValueError as exc:
        assert str(exc) == "Redis key must not be empty"
    else:
        raise AssertionError("Expected key validation error")
