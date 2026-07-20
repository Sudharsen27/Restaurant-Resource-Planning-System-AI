"""Category service."""

from __future__ import annotations

import re
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.enterprise import Category
from app.repositories.category_repository import CategoryRepository
from app.repositories.restaurant_repository import RestaurantRepository
from app.schemas.category import CategoryCreate, CategoryOut, CategoryUpdate


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug[:100] or "category"


def _to_out(row: Category) -> CategoryOut:
    return CategoryOut(
        id=row.id,
        restaurant_id=row.restaurant_id,
        parent_id=row.parent_id,
        name=row.name,
        slug=row.slug,
        description=row.description,
        image_url=row.image_url,
        sort_order=row.sort_order or 0,
        is_active=row.is_active,
        status="active" if row.is_active and not row.is_deleted else "inactive",
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class CategoryService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = CategoryRepository(db)
        self.restaurants = RestaurantRepository(db)

    def list_categories(self, **kwargs) -> list[CategoryOut]:
        return [_to_out(r) for r in self.repo.list_filtered(**kwargs)]

    def get_category(self, category_id: UUID) -> CategoryOut:
        row = self.repo.get_by_id(category_id)
        if row is None:
            raise NotFoundError("Category", str(category_id))
        return _to_out(row)

    def create_category(self, payload: CategoryCreate, *, actor_id: int | None = None) -> CategoryOut:
        if self.restaurants.get_by_id(payload.restaurant_id) is None:
            raise NotFoundError("Restaurant", str(payload.restaurant_id))
        name = payload.name.strip()
        if not name:
            raise ValidationError("Category name is required")
        slug = (payload.slug or _slugify(name)).strip().lower()
        if self.repo.get_by_slug(payload.restaurant_id, slug):
            raise ConflictError(f"Category slug '{slug}' already exists for this restaurant")
        row = Category(
            restaurant_id=payload.restaurant_id,
            parent_id=payload.parent_id,
            name=name,
            slug=slug,
            description=payload.description,
            image_url=payload.image_url,
            sort_order=payload.sort_order,
            is_active=payload.is_active,
            created_by=actor_id,
            updated_by=actor_id,
        )
        return _to_out(self.repo.add(row))

    def update_category(
        self,
        category_id: UUID,
        payload: CategoryUpdate,
        *,
        actor_id: int | None = None,
    ) -> CategoryOut:
        row = self.repo.get_by_id(category_id)
        if row is None:
            raise NotFoundError("Category", str(category_id))
        data = payload.model_dump(exclude_unset=True)
        restaurant_id = data.get("restaurant_id", row.restaurant_id)
        if "restaurant_id" in data and data["restaurant_id"] is not None:
            if self.restaurants.get_by_id(data["restaurant_id"]) is None:
                raise NotFoundError("Restaurant", str(data["restaurant_id"]))
        if "name" in data and data["name"] is not None:
            data["name"] = data["name"].strip()
        if "slug" in data and data["slug"] is not None:
            slug = data["slug"].strip().lower()
            if self.repo.get_by_slug(restaurant_id, slug, exclude_id=category_id):
                raise ConflictError(f"Category slug '{slug}' already exists for this restaurant")
            data["slug"] = slug
        for key, value in data.items():
            setattr(row, key, value)
        row.updated_by = actor_id
        return _to_out(self.repo.save(row))

    def delete_category(self, category_id: UUID, *, actor_id: int | None = None) -> None:
        row = self.repo.get_by_id(category_id)
        if row is None:
            raise NotFoundError("Category", str(category_id))
        row.updated_by = actor_id
        self.repo.soft_delete(row)
