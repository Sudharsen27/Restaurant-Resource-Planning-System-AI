"""Product-specific cache policy built on the reusable RedisService."""

from __future__ import annotations

import hashlib
import logging
from typing import Any, Protocol, Sequence
from uuid import UUID

from fastapi import Depends
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.product import ProductOut
from app.services.redis_service import RedisService, get_redis_service

logger = logging.getLogger(__name__)


class JsonCache(Protocol):
    """Minimal cache interface required by ProductCacheService."""

    def get_json(self, key: str) -> Any | None: ...

    def set_json(self, key: str, value: Any, *, ttl_seconds: int | None = None) -> bool: ...

    def delete(self, key: str) -> bool: ...


class ProductCacheService:
    """Cache policy for serialized ProductOut list responses.

    This service does not query the database and never receives SQLAlchemy ORM
    objects. ProductService will later decide when to read or populate it.
    """

    CACHE_VERSION = "v1"
    CACHE_NAMESPACE = "catalog:products"

    def __init__(
        self,
        cache: JsonCache,
        *,
        ttl_seconds: int | None = None,
    ) -> None:
        self._cache = cache
        self._ttl_seconds = ttl_seconds or settings.redis_cache_default_ttl_seconds
        if self._ttl_seconds <= 0:
            raise ValueError("Product cache TTL must be greater than zero")

    def get_product_list(
        self,
        *,
        restaurant_id: UUID,
        category_id: UUID | None = None,
        active_only: bool = False,
        search: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[ProductOut] | None:
        """Return a validated product DTO list or None on a cache miss."""
        key = self._build_list_key(
            restaurant_id=restaurant_id,
            category_id=category_id,
            active_only=active_only,
            search=search,
            offset=offset,
            limit=limit,
        )
        payload = self._cache.get_json(key)
        if payload is None:
            logger.debug(
                "Product list cache miss",
                extra={"event": "product_cache_miss", "cache_key": key},
            )
            return None

        if not isinstance(payload, list):
            logger.warning(
                "Product list cache payload has an unexpected shape",
                extra={"event": "product_cache_payload_invalid", "cache_key": key},
            )
            self._cache.delete(key)
            return None

        try:
            products = [ProductOut.model_validate(item) for item in payload]
        except ValidationError:
            logger.warning(
                "Product list cache payload failed DTO validation",
                extra={"event": "product_cache_payload_invalid", "cache_key": key},
                exc_info=True,
            )
            self._cache.delete(key)
            return None

        logger.debug(
            "Product list cache hit",
            extra={
                "event": "product_cache_hit",
                "cache_key": key,
                "item_count": len(products),
            },
        )
        return products

    def set_product_list(
        self,
        products: Sequence[ProductOut],
        *,
        restaurant_id: UUID,
        category_id: UUID | None = None,
        active_only: bool = False,
        search: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> bool:
        """Store serialized ProductOut DTOs for one deterministic list query."""
        key = self._build_list_key(
            restaurant_id=restaurant_id,
            category_id=category_id,
            active_only=active_only,
            search=search,
            offset=offset,
            limit=limit,
        )
        payload = [product.model_dump(mode="json") for product in products]
        stored = self._cache.set_json(key, payload, ttl_seconds=self._ttl_seconds)
        logger.debug(
            "Product list cache write completed",
            extra={
                "event": "product_cache_set",
                "cache_key": key,
                "item_count": len(payload),
                "ttl_seconds": self._ttl_seconds,
                "stored": stored,
            },
        )
        return stored

    def invalidate_product_list(
        self,
        *,
        restaurant_id: UUID,
        category_id: UUID | None = None,
        active_only: bool = False,
        search: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> bool:
        """Invalidate one exact product-list cache variant.

        A future ProductService integration can call this for known filter
        variants or adopt generation-based invalidation for all variants.
        """
        key = self._build_list_key(
            restaurant_id=restaurant_id,
            category_id=category_id,
            active_only=active_only,
            search=search,
            offset=offset,
            limit=limit,
        )
        deleted = self._cache.delete(key)
        logger.info(
            "Product list cache invalidated",
            extra={
                "event": "product_cache_list_invalidated",
                "cache_key": key,
                "deleted": deleted,
            },
        )
        return deleted

    def invalidate_product(self, product_id: UUID) -> bool:
        """Invalidate a future product-detail cache entry."""
        key = self._build_product_key(product_id)
        deleted = self._cache.delete(key)
        logger.info(
            "Product detail cache invalidated",
            extra={
                "event": "product_cache_detail_invalidated",
                "cache_key": key,
                "deleted": deleted,
            },
        )
        return deleted

    @classmethod
    def _build_list_key(
        cls,
        *,
        restaurant_id: UUID,
        category_id: UUID | None,
        active_only: bool,
        search: str | None,
        offset: int,
        limit: int,
    ) -> str:
        if offset < 0:
            raise ValueError("offset must not be negative")
        if limit < 1:
            raise ValueError("limit must be greater than zero")

        category = str(category_id) if category_id else "all"
        normalized_search = " ".join(search.strip().lower().split()) if search else ""
        search_token = hashlib.sha256(normalized_search.encode("utf-8")).hexdigest()[:16]
        return (
            f"{cls.CACHE_NAMESPACE}:{cls.CACHE_VERSION}:"
            f"restaurant:{restaurant_id}:"
            f"category:{category}:"
            f"active:{int(active_only)}:"
            f"search:{search_token}:"
            f"offset:{offset}:"
            f"limit:{limit}"
        )

    @classmethod
    def _build_product_key(cls, product_id: UUID) -> str:
        return f"{cls.CACHE_NAMESPACE}:{cls.CACHE_VERSION}:product:{product_id}"


def get_product_cache_service(
    redis_service: RedisService = Depends(get_redis_service),
) -> ProductCacheService:
    """FastAPI dependency provider for ProductCacheService."""
    return ProductCacheService(redis_service)
