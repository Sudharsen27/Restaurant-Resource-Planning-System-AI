"""Reusable Redis JSON service with dependency-injection support.

This module deliberately owns Redis transport concerns only. Domain services
decide cache keys, TTL policy, and invalidation semantics.
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from typing import Any, Protocol, TypeVar

from app.core.config import settings

logger = logging.getLogger(__name__)

JsonValue = dict[str, Any] | list[Any] | str | int | float | bool | None
T = TypeVar("T")


class RedisClient(Protocol):
    """Minimal redis-py surface required by RedisService."""

    def get(self, name: str) -> str | bytes | None: ...

    def set(self, name: str, value: str, ex: int | None = None) -> bool | None: ...

    def delete(self, *names: str) -> int: ...

    def exists(self, *names: str) -> int: ...

    def ping(self) -> bool: ...


class RedisService:
    """Fail-open JSON wrapper around redis-py.

    Redis errors are logged and converted to safe return values so an optional
    cache cannot make a database-backed application unavailable.
    """

    def __init__(self, client: RedisClient | None, *, key_prefix: str) -> None:
        self._client = client
        self._key_prefix = key_prefix.strip(":")

    @property
    def available(self) -> bool:
        """Whether a Redis client has been configured."""
        return self._client is not None

    def get_json(self, key: str) -> T | None:
        """Read and deserialize JSON; return None on a miss or Redis failure."""
        client = self._client
        if client is None:
            return None

        redis_key = self._build_key(key)
        try:
            raw = client.get(redis_key)
            if raw is None:
                return None
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8")
            return json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            logger.warning(
                "Redis JSON payload is invalid",
                extra={"event": "redis_json_decode_error", "redis_key": redis_key},
                exc_info=exc,
            )
            return None
        except Exception:
            logger.exception(
                "Redis JSON read failed",
                extra={"event": "redis_get_error", "redis_key": redis_key},
            )
            return None

    def set_json(self, key: str, value: JsonValue, *, ttl_seconds: int | None = None) -> bool:
        """Serialize and write JSON with an optional positive TTL."""
        client = self._client
        if client is None:
            return False
        if ttl_seconds is not None and ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be greater than zero")

        redis_key = self._build_key(key)
        try:
            payload = json.dumps(value, default=str, separators=(",", ":"))
        except (TypeError, ValueError):
            logger.exception(
                "Redis JSON serialization failed",
                extra={"event": "redis_json_encode_error", "redis_key": redis_key},
            )
            return False

        try:
            result = client.set(redis_key, payload, ex=ttl_seconds)
            return result is not False
        except Exception:
            logger.exception(
                "Redis JSON write failed",
                extra={"event": "redis_set_error", "redis_key": redis_key},
            )
            return False

    def delete(self, key: str) -> bool:
        """Delete a value and return whether Redis removed a key."""
        client = self._client
        if client is None:
            return False

        redis_key = self._build_key(key)
        try:
            return client.delete(redis_key) > 0
        except Exception:
            logger.exception(
                "Redis delete failed",
                extra={"event": "redis_delete_error", "redis_key": redis_key},
            )
            return False

    def exists(self, key: str) -> bool:
        """Return whether a key exists without retrieving its payload."""
        client = self._client
        if client is None:
            return False

        redis_key = self._build_key(key)
        try:
            return client.exists(redis_key) > 0
        except Exception:
            logger.exception(
                "Redis exists check failed",
                extra={"event": "redis_exists_error", "redis_key": redis_key},
            )
            return False

    def ping(self) -> bool:
        """Return Redis health without raising a connection error."""
        client = self._client
        if client is None:
            return False

        try:
            return bool(client.ping())
        except Exception:
            logger.warning("Redis ping failed", extra={"event": "redis_ping_error"}, exc_info=True)
            return False

    def _build_key(self, key: str) -> str:
        normalized_key = key.strip(":")
        if not normalized_key:
            raise ValueError("Redis key must not be empty")
        return f"{self._key_prefix}:{normalized_key}" if self._key_prefix else normalized_key


def _create_redis_client() -> RedisClient | None:
    """Create the redis-py client from application configuration."""
    if not settings.redis_enabled:
        return None

    try:
        import redis

        return redis.Redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
            health_check_interval=30,
        )
    except Exception:
        logger.exception("Redis client initialization failed", extra={"event": "redis_client_init_error"})
        return None


@lru_cache(maxsize=1)
def get_redis_service() -> RedisService:
    """FastAPI-compatible dependency provider for the shared Redis service."""
    return RedisService(_create_redis_client(), key_prefix=settings.redis_key_prefix)
