from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import UUID

from app.schemas.product import ProductCreate, ProductOut, ProductUpdate
from app.services import product_service
from app.services.product_service import ProductService

RESTAURANT_ID = UUID("00000000-0000-0000-0000-000000000001")
PRODUCT_ID = UUID("00000000-0000-0000-0000-000000000003")


class FakeProductCache:
    def __init__(
        self,
        cached: list[ProductOut] | None = None,
        *,
        stores: bool = True,
        invalidates: bool = True,
        invalidation_error: Exception | None = None,
    ) -> None:
        self.cached = cached
        self.stores = stores
        self.invalidates = invalidates
        self.invalidation_error = invalidation_error
        self.get_calls: list[dict] = []
        self.set_calls: list[tuple[list[ProductOut], dict]] = []
        self.invalidation_calls: list[dict] = []

    def get_product_list(self, **kwargs) -> list[ProductOut] | None:
        self.get_calls.append(kwargs)
        return self.cached

    def set_product_list(self, products: list[ProductOut], **kwargs) -> bool:
        self.set_calls.append((products, kwargs))
        return self.stores

    def invalidate_product_list(self, **kwargs) -> bool:
        self.invalidation_calls.append(kwargs)
        if self.invalidation_error:
            raise self.invalidation_error
        return self.invalidates


def product_dto() -> ProductOut:
    now = datetime(2026, 8, 6, tzinfo=UTC)
    return ProductOut(
        id=PRODUCT_ID,
        restaurant_id=RESTAURANT_ID,
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


def test_list_products_returns_cached_dtos_without_querying_repository():
    cached = [product_dto()]
    cache = FakeProductCache(cached)
    service = ProductService(db=None, product_cache=cache)
    service.repo.list_filtered = Mock(side_effect=AssertionError("Repository must not run on a cache hit"))

    result = service.list_products(restaurant_id=RESTAURANT_ID, skip=10, limit=25)

    assert result == cached
    assert cache.get_calls == [
        {
            "restaurant_id": RESTAURANT_ID,
            "category_id": None,
            "active_only": False,
            "search": None,
            "offset": 10,
            "limit": 25,
        }
    ]
    assert cache.set_calls == []


def test_list_products_queries_database_then_stores_successful_response():
    cache = FakeProductCache()
    service = ProductService(db=None, product_cache=cache)
    service.repo.list_filtered = Mock(return_value=[])

    result = service.list_products(restaurant_id=RESTAURANT_ID, active_only=True)

    assert result == []
    service.repo.list_filtered.assert_called_once_with(
        restaurant_id=RESTAURANT_ID,
        active_only=True,
    )
    assert cache.set_calls == [
        (
            [],
            {
                "restaurant_id": RESTAURANT_ID,
                "category_id": None,
                "active_only": True,
                "search": None,
                "offset": 0,
                "limit": 100,
            },
        )
    ]


def test_list_products_falls_back_to_database_when_cache_read_raises():
    cache = FakeProductCache()
    cache.get_product_list = Mock(side_effect=ConnectionError("Redis unavailable"))
    service = ProductService(db=None, product_cache=cache)
    service.repo.list_filtered = Mock(return_value=[])

    assert service.list_products(restaurant_id=RESTAURANT_ID) == []
    service.repo.list_filtered.assert_called_once_with(restaurant_id=RESTAURANT_ID)


def test_list_products_bypasses_cache_without_restaurant_scope():
    cache = FakeProductCache()
    service = ProductService(db=None, product_cache=cache)
    service.repo.list_filtered = Mock(return_value=[])

    assert service.list_products() == []
    service.repo.list_filtered.assert_called_once_with()
    assert cache.get_calls == []
    assert cache.set_calls == []


def _mutation_service(monkeypatch, cache: FakeProductCache) -> ProductService:
    monkeypatch.setattr(product_service, "write_audit", Mock())
    service = ProductService(db=Mock(), product_cache=cache)
    service.restaurants.get_by_id = Mock(return_value=object())
    service.categories.get_by_id = Mock(return_value=object())
    service.repo.get_by_sku = Mock(return_value=None)
    service.get_product = Mock(return_value=product_dto())
    return service


def test_create_product_invalidates_cache_after_commit(monkeypatch):
    cache = FakeProductCache()
    service = _mutation_service(monkeypatch, cache)
    service.repo.add = Mock(
        return_value=SimpleNamespace(id=PRODUCT_ID, restaurant_id=RESTAURANT_ID),
    )

    service.create_product(
        ProductCreate(restaurant_id=RESTAURANT_ID, name="Masala Tea", sku="TEA-001"),
    )

    assert cache.invalidation_calls == [{"restaurant_id": RESTAURANT_ID}]


def test_update_product_invalidates_cache_after_commit(monkeypatch):
    cache = FakeProductCache()
    service = _mutation_service(monkeypatch, cache)
    service.repo.get_by_id = Mock(
        return_value=SimpleNamespace(
            id=PRODUCT_ID,
            restaurant_id=RESTAURANT_ID,
            updated_by=None,
        ),
    )
    service.repo.save = Mock()

    service.update_product(PRODUCT_ID, ProductUpdate(name="Updated Tea"))

    assert cache.invalidation_calls == [{"restaurant_id": RESTAURANT_ID}]


def test_delete_product_invalidates_cache_after_commit(monkeypatch):
    cache = FakeProductCache()
    service = _mutation_service(monkeypatch, cache)
    row = SimpleNamespace(
        id=PRODUCT_ID,
        restaurant_id=RESTAURANT_ID,
        sku="TEA-001",
        updated_by=None,
    )
    service.repo.get_by_id = Mock(return_value=row)
    service.repo.soft_delete = Mock()
    catalog_service = Mock(unsafe=True)
    monkeypatch.setattr(product_service, "CatalogService", Mock(return_value=catalog_service))

    service.delete_product(PRODUCT_ID)

    assert cache.invalidation_calls == [{"restaurant_id": RESTAURANT_ID}]


def test_cache_invalidation_failure_does_not_fail_product_create(monkeypatch):
    cache = FakeProductCache(invalidation_error=ConnectionError("Redis unavailable"))
    service = _mutation_service(monkeypatch, cache)
    service.repo.add = Mock(
        return_value=SimpleNamespace(id=PRODUCT_ID, restaurant_id=RESTAURANT_ID),
    )

    result = service.create_product(
        ProductCreate(restaurant_id=RESTAURANT_ID, name="Masala Tea", sku="TEA-001"),
    )

    assert result == product_dto()
    assert cache.invalidation_calls == [{"restaurant_id": RESTAURANT_ID}]
