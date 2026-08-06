from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from app.schemas.product import ProductOut
from app.services.product_cache_service import ProductCacheService

RESTAURANT_ID = UUID("00000000-0000-0000-0000-000000000001")
CATEGORY_ID = UUID("00000000-0000-0000-0000-000000000002")
PRODUCT_ID = UUID("00000000-0000-0000-0000-000000000003")


class FakeJsonCache:
    def __init__(self) -> None:
        self.values: dict[str, object] = {}
        self.last_ttl: int | None = None
        self.deleted_keys: list[str] = []

    def get_json(self, key: str):
        return self.values.get(key)

    def set_json(self, key: str, value: object, *, ttl_seconds: int | None = None) -> bool:
        self.values[key] = value
        self.last_ttl = ttl_seconds
        return True

    def delete(self, key: str) -> bool:
        self.deleted_keys.append(key)
        return self.values.pop(key, None) is not None


def product_dto() -> ProductOut:
    now = datetime(2026, 8, 6, tzinfo=UTC)
    return ProductOut(
        id=PRODUCT_ID,
        restaurant_id=RESTAURANT_ID,
        category_id=CATEGORY_ID,
        category="Beverages",
        name="Masala Tea",
        sku="TEA-001",
        unit="cup",
        unit_cost=Decimal("10.00"),
        unit_price=Decimal("30.00"),
        price=Decimal("30.00"),
        is_active=True,
        status="Active",
        created_at=now,
        updated_at=now,
    )


def test_product_list_round_trips_serialized_dtos():
    cache = FakeJsonCache()
    service = ProductCacheService(cache, ttl_seconds=300)

    assert service.set_product_list(
        [product_dto()],
        restaurant_id=RESTAURANT_ID,
        category_id=CATEGORY_ID,
        active_only=True,
        search="Masala tea",
        offset=0,
        limit=25,
    )
    cached = service.get_product_list(
        restaurant_id=RESTAURANT_ID,
        category_id=CATEGORY_ID,
        active_only=True,
        search="  MASALA   TEA ",
        offset=0,
        limit=25,
    )

    assert cache.last_ttl == 300
    assert cached == [product_dto()]
    assert isinstance(next(iter(cache.values.values())), list)
    assert isinstance(next(iter(cache.values.values()))[0], dict)


def test_product_list_key_changes_with_each_response_filter():
    common = {
        "restaurant_id": RESTAURANT_ID,
        "category_id": CATEGORY_ID,
        "active_only": True,
        "search": "tea",
        "offset": 0,
        "limit": 25,
    }
    base_key = ProductCacheService._build_list_key(**common)

    assert base_key != ProductCacheService._build_list_key(**{**common, "active_only": False})
    assert base_key != ProductCacheService._build_list_key(**{**common, "search": "coffee"})
    assert base_key != ProductCacheService._build_list_key(**{**common, "offset": 25})
    assert base_key != ProductCacheService._build_list_key(**{**common, "limit": 50})


def test_invalidating_product_list_uses_the_matching_key():
    cache = FakeJsonCache()
    service = ProductCacheService(cache, ttl_seconds=300)
    service.set_product_list([product_dto()], restaurant_id=RESTAURANT_ID)

    assert service.invalidate_product_list(restaurant_id=RESTAURANT_ID)
    assert cache.deleted_keys[-1].startswith("catalog:products:v1:restaurant:")


def test_invalidating_product_deletes_future_detail_key():
    cache = FakeJsonCache()
    service = ProductCacheService(cache, ttl_seconds=300)

    assert not service.invalidate_product(PRODUCT_ID)
    assert cache.deleted_keys == [f"catalog:products:v1:product:{PRODUCT_ID}"]


def test_invalid_cached_payload_is_deleted_and_treated_as_miss():
    cache = FakeJsonCache()
    service = ProductCacheService(cache, ttl_seconds=300)
    key = service._build_list_key(
        restaurant_id=RESTAURANT_ID,
        category_id=None,
        active_only=False,
        search=None,
        offset=0,
        limit=100,
    )
    cache.values[key] = [{"id": "not-a-uuid"}]

    assert service.get_product_list(restaurant_id=RESTAURANT_ID) is None
    assert cache.deleted_keys == [key]
