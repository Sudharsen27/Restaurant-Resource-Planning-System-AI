"""Product service."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.enterprise import Product
from app.models.enums import AuditAction, ProductLifecycleStatus
from app.repositories.category_repository import CategoryRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.restaurant_repository import RestaurantRepository
from app.schemas.product import ProductCreate, ProductOut, ProductUpdate
from app.services.audit_service import write_audit
from app.services.catalog_service import CatalogService


def _to_out(row: Product) -> ProductOut:
    lifecycle = (
        row.lifecycle_status.value
        if hasattr(row.lifecycle_status, "value")
        else str(getattr(row, "lifecycle_status", "ACTIVE"))
    )
    return ProductOut(
        id=row.id,
        restaurant_id=row.restaurant_id,
        category_id=row.category_id,
        category=row.category.name if row.category else None,
        supplier_id=row.supplier_id,
        supplier=row.supplier.name if row.supplier else None,
        uom_id=row.uom_id,
        name=row.name,
        sku=row.sku,
        barcode=row.barcode,
        brand=row.brand,
        description=row.description,
        unit=row.unit,
        unit_cost=row.unit_cost,
        unit_price=row.unit_price,
        tax_rate=getattr(row, "tax_rate", 0) or 0,
        hsn_code=row.hsn_code,
        image_url=row.image_url,
        lifecycle_status=lifecycle,
        price=row.unit_price,
        is_active=row.is_active,
        status=lifecycle.title() if lifecycle else ("Active" if row.is_active else "Inactive"),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class ProductService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ProductRepository(db)
        self.restaurants = RestaurantRepository(db)
        self.categories = CategoryRepository(db)

    def list_products(self, **kwargs) -> list[ProductOut]:
        return [_to_out(r) for r in self.repo.list_filtered(**kwargs)]

    def get_product(self, product_id: UUID) -> ProductOut:
        row = self.repo.get_by_id(product_id)
        if row is None:
            raise NotFoundError("Product", str(product_id))
        return _to_out(row)

    def create_product(self, payload: ProductCreate, *, actor_id: int | None = None) -> ProductOut:
        if self.restaurants.get_by_id(payload.restaurant_id) is None:
            raise NotFoundError("Restaurant", str(payload.restaurant_id))
        if payload.category_id and self.categories.get_by_id(payload.category_id) is None:
            raise NotFoundError("Category", str(payload.category_id))
        name = payload.name.strip()
        sku = payload.sku.strip().upper()
        if not name:
            raise ValidationError("Product name is required")
        if self.repo.get_by_sku(payload.restaurant_id, sku):
            raise ConflictError(f"SKU '{sku}' already exists for this restaurant")
        row = Product(
            restaurant_id=payload.restaurant_id,
            category_id=payload.category_id,
            supplier_id=payload.supplier_id,
            uom_id=payload.uom_id,
            name=name,
            sku=sku,
            barcode=payload.barcode,
            brand=payload.brand,
            description=payload.description,
            unit=payload.unit,
            unit_cost=payload.unit_cost,
            unit_price=payload.unit_price,
            tax_rate=payload.tax_rate,
            hsn_code=payload.hsn_code,
            image_url=payload.image_url,
            lifecycle_status=payload.lifecycle_status,
            is_active=payload.is_active and payload.lifecycle_status == ProductLifecycleStatus.ACTIVE,
            created_by=actor_id,
            updated_by=actor_id,
        )
        created = self.repo.add(row)
        write_audit(
            self.db,
            action=AuditAction.CREATE,
            actor_user_id=actor_id,
            entity_type="Product",
            entity_id=str(created.id),
            details={"sku": sku, "name": name},
            commit=True,
        )
        return self.get_product(created.id)

    def update_product(
        self,
        product_id: UUID,
        payload: ProductUpdate,
        *,
        actor_id: int | None = None,
    ) -> ProductOut:
        row = self.repo.get_by_id(product_id)
        if row is None:
            raise NotFoundError("Product", str(product_id))
        data = payload.model_dump(exclude_unset=True)
        restaurant_id = data.get("restaurant_id", row.restaurant_id)
        if "restaurant_id" in data and data["restaurant_id"] is not None:
            if self.restaurants.get_by_id(data["restaurant_id"]) is None:
                raise NotFoundError("Restaurant", str(data["restaurant_id"]))
        if "category_id" in data and data["category_id"] is not None:
            if self.categories.get_by_id(data["category_id"]) is None:
                raise NotFoundError("Category", str(data["category_id"]))
        if "name" in data and data["name"] is not None:
            data["name"] = data["name"].strip()
        if "sku" in data and data["sku"] is not None:
            sku = data["sku"].strip().upper()
            if self.repo.get_by_sku(restaurant_id, sku, exclude_id=product_id):
                raise ConflictError(f"SKU '{sku}' already exists for this restaurant")
            data["sku"] = sku
        if "lifecycle_status" in data and data["lifecycle_status"] is not None:
            status = data["lifecycle_status"]
            if status != ProductLifecycleStatus.ACTIVE:
                data["is_active"] = False
        for key, value in data.items():
            setattr(row, key, value)
        row.updated_by = actor_id
        self.repo.save(row)
        write_audit(
            self.db,
            action=AuditAction.UPDATE,
            actor_user_id=actor_id,
            entity_type="Product",
            entity_id=str(product_id),
            details={k: (str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v) for k, v in data.items()},
            commit=True,
        )
        return self.get_product(product_id)

    def delete_product(self, product_id: UUID, *, actor_id: int | None = None) -> None:
        row = self.repo.get_by_id(product_id)
        if row is None:
            raise NotFoundError("Product", str(product_id))
        CatalogService(self.db).assert_can_delete_product(product_id)
        row.updated_by = actor_id
        self.repo.soft_delete(row)
        write_audit(
            self.db,
            action=AuditAction.DELETE,
            actor_user_id=actor_id,
            entity_type="Product",
            entity_id=str(product_id),
            details={"sku": row.sku},
            commit=True,
        )

    def export_csv(
        self,
        *,
        restaurant_id: UUID | None = None,
        skip: int = 0,
        limit: int = 5000,
    ) -> str:
        import csv
        import io

        rows = self.repo.list_filtered(
            restaurant_id=restaurant_id, skip=skip, limit=limit, active_only=False
        )
        buf = io.StringIO()
        writer = csv.DictWriter(
            buf,
            fieldnames=[
                "sku",
                "name",
                "barcode",
                "brand",
                "unit",
                "unit_cost",
                "unit_price",
                "tax_rate",
                "hsn_code",
                "lifecycle_status",
                "category",
                "supplier",
            ],
        )
        writer.writeheader()
        for r in rows:
            writer.writerow(
                {
                    "sku": r.sku,
                    "name": r.name,
                    "barcode": r.barcode or "",
                    "brand": r.brand or "",
                    "unit": r.unit,
                    "unit_cost": str(r.unit_cost),
                    "unit_price": str(r.unit_price),
                    "tax_rate": str(getattr(r, "tax_rate", 0) or 0),
                    "hsn_code": r.hsn_code or "",
                    "lifecycle_status": (
                        r.lifecycle_status.value
                        if hasattr(r.lifecycle_status, "value")
                        else str(r.lifecycle_status)
                    ),
                    "category": r.category.name if r.category else "",
                    "supplier": r.supplier.name if r.supplier else "",
                }
            )
        return buf.getvalue()

    def import_csv(
        self,
        *,
        restaurant_id: UUID,
        csv_text: str,
        actor_id: int | None = None,
    ) -> dict:
        import csv
        import io
        from decimal import Decimal, InvalidOperation

        if self.restaurants.get_by_id(restaurant_id) is None:
            raise NotFoundError("Restaurant", str(restaurant_id))

        reader = csv.DictReader(io.StringIO(csv_text))
        created = 0
        updated = 0
        errors: list[str] = []
        for idx, row in enumerate(reader, start=2):
            try:
                sku = (row.get("sku") or "").strip().upper()
                name = (row.get("name") or "").strip()
                if not sku or not name:
                    errors.append(f"Row {idx}: sku and name are required")
                    continue
                unit_cost = Decimal(str(row.get("unit_cost") or "0"))
                unit_price = Decimal(str(row.get("unit_price") or "0"))
                tax_rate = Decimal(str(row.get("tax_rate") or "0"))
                existing = self.repo.get_by_sku(restaurant_id, sku)
                if existing:
                    existing.name = name
                    existing.barcode = (row.get("barcode") or None) or existing.barcode
                    existing.brand = (row.get("brand") or None) or existing.brand
                    existing.unit = (row.get("unit") or existing.unit or "pcs").strip()
                    existing.unit_cost = unit_cost
                    existing.unit_price = unit_price
                    existing.tax_rate = tax_rate
                    existing.hsn_code = (row.get("hsn_code") or None) or existing.hsn_code
                    existing.updated_by = actor_id
                    self.repo.save(existing)
                    updated += 1
                else:
                    payload = ProductCreate(
                        restaurant_id=restaurant_id,
                        name=name,
                        sku=sku,
                        barcode=(row.get("barcode") or None) or None,
                        brand=(row.get("brand") or None) or None,
                        unit=(row.get("unit") or "pcs").strip(),
                        unit_cost=unit_cost,
                        unit_price=unit_price,
                        tax_rate=tax_rate,
                        hsn_code=(row.get("hsn_code") or None) or None,
                    )
                    self.create_product(payload, actor_id=actor_id)
                    created += 1
            except (ValidationError, ConflictError, InvalidOperation, ValueError) as exc:
                errors.append(f"Row {idx}: {exc}")
            except Exception as exc:  # noqa: BLE001
                errors.append(f"Row {idx}: {exc}")
        return {"created": created, "updated": updated, "errors": errors}
