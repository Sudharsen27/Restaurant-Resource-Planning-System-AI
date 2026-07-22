"""Redis-backed cache, session, and temporary-data helpers with in-memory fallback."""

from __future__ import annotations

import json
import logging
import threading
import time
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)


class _MemoryStore:
    """Process-local fallback when Redis is unavailable."""

    def __init__(self) -> None:
        self._data: dict[str, tuple[Any, float | None]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            item = self._data.get(key)
            if not item:
                return None
            value, expires_at = item
            if expires_at is not None and expires_at <= time.time():
                self._data.pop(key, None)
                return None
            return value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        expires_at = (time.time() + ttl) if ttl else None
        with self._lock:
            self._data[key] = (value, expires_at)

    def delete(self, key: str) -> None:
        with self._lock:
            self._data.pop(key, None)

    def clear_prefix(self, prefix: str) -> int:
        with self._lock:
            keys = [k for k in self._data if k.startswith(prefix)]
            for k in keys:
                del self._data[k]
            return len(keys)

    def ping(self) -> bool:
        return True


class CacheService:
    """Unified cache API: Redis when healthy, otherwise in-memory."""

    def __init__(self) -> None:
        self._redis = None
        self._memory = _MemoryStore()
        self._backend = "memory"
        if settings.redis_enabled:
            self._connect()

    def _connect(self) -> None:
        try:
            import redis

            client = redis.Redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
            client.ping()
            self._redis = client
            self._backend = "redis"
            logger.info("Redis cache connected", extra={"event": "redis_connected"})
        except Exception:
            self._redis = None
            self._backend = "memory"
            logger.warning(
                "Redis unavailable — using in-memory cache",
                extra={"event": "redis_fallback"},
            )

    def _key(self, namespace: str, key: str) -> str:
        return f"{settings.redis_key_prefix}:{namespace}:{key}"

    @property
    def backend(self) -> str:
        return self._backend

    def ping(self) -> bool:
        if self._redis is not None:
            try:
                return bool(self._redis.ping())
            except Exception:
                return False
        return self._memory.ping()

    def get(self, namespace: str, key: str) -> Any | None:
        full = self._key(namespace, key)
        if self._redis is not None:
            try:
                raw = self._redis.get(full)
                if raw is None:
                    return None
                return json.loads(raw)
            except Exception:
                logger.exception("Redis get failed", extra={"event": "redis_get_error", "key": full})
                return None
        return self._memory.get(full)

    def set(
        self,
        namespace: str,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> None:
        full = self._key(namespace, key)
        ttl = ttl if ttl is not None else settings.redis_cache_default_ttl_seconds
        if self._redis is not None:
            try:
                payload = json.dumps(value, default=str)
                if ttl and ttl > 0:
                    self._redis.setex(full, ttl, payload)
                else:
                    self._redis.set(full, payload)
                return
            except Exception:
                logger.exception("Redis set failed", extra={"event": "redis_set_error", "key": full})
        self._memory.set(full, value, ttl=ttl if ttl and ttl > 0 else None)

    def delete(self, namespace: str, key: str) -> None:
        full = self._key(namespace, key)
        if self._redis is not None:
            try:
                self._redis.delete(full)
                return
            except Exception:
                logger.exception("Redis delete failed", extra={"event": "redis_delete_error"})
        self._memory.delete(full)

    def clear_namespace(self, namespace: str) -> int:
        prefix = self._key(namespace, "")
        if self._redis is not None:
            try:
                deleted = 0
                cursor = 0
                pattern = f"{prefix}*"
                while True:
                    cursor, keys = self._redis.scan(cursor=cursor, match=pattern, count=200)
                    if keys:
                        deleted += int(self._redis.delete(*keys))
                    if cursor == 0:
                        break
                return deleted
            except Exception:
                logger.exception("Redis clear failed", extra={"event": "redis_clear_error"})
                return 0
        return self._memory.clear_prefix(prefix)

    # Convenience namespaces -------------------------------------------------

    def cache_get(self, key: str) -> Any | None:
        return self.get("cache", key)

    def cache_set(self, key: str, value: Any, ttl: int | None = None) -> None:
        self.set("cache", key, value, ttl=ttl)

    def session_get(self, session_id: str) -> Any | None:
        return self.get("session", session_id)

    def session_set(self, session_id: str, value: Any, ttl: int | None = None) -> None:
        self.set(
            "session",
            session_id,
            value,
            ttl=ttl or settings.redis_session_ttl_seconds,
        )

    def session_delete(self, session_id: str) -> None:
        self.delete("session", session_id)

    def temp_set(self, key: str, value: Any, ttl: int = 600) -> None:
        self.set("temp", key, value, ttl=ttl)

    def temp_get(self, key: str) -> Any | None:
        return self.get("temp", key)

    def rate_limit_hit(self, bucket: str, limit: int, window_seconds: int) -> tuple[bool, int]:
        """Return (allowed, remaining). Sliding window via Redis INCR or memory."""
        full = self._key("ratelimit", bucket)
        if self._redis is not None:
            try:
                pipe = self._redis.pipeline()
                pipe.incr(full)
                pipe.ttl(full)
                count, ttl = pipe.execute()
                if ttl == -1:
                    self._redis.expire(full, window_seconds)
                remaining = max(0, limit - int(count))
                return int(count) <= limit, remaining
            except Exception:
                logger.exception("Redis rate limit failed", extra={"event": "redis_ratelimit_error"})
        # Memory fallback
        count_key = f"{full}:count"
        start_key = f"{full}:start"
        now = time.time()
        start = self._memory.get(start_key)
        if start is None or now - float(start) >= window_seconds:
            self._memory.set(start_key, now, ttl=window_seconds)
            self._memory.set(count_key, 1, ttl=window_seconds)
            return True, limit - 1
        count = int(self._memory.get(count_key) or 0) + 1
        self._memory.set(count_key, count, ttl=window_seconds)
        remaining = max(0, limit - count)
        return count <= limit, remaining


_cache_service: CacheService | None = None


def get_cache_service() -> CacheService:
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service
