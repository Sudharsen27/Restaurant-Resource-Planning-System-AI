"""Restaurant operations APIs — dining areas, tables, departments, settings, documents."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models import User
from app.models.enums import DocumentType, TableStatus
from app.schemas.operations import (
    BusinessSettingsUpsert,
    DepartmentCreate,
    DepartmentUpdate,
    DiningAreaCreate,
    DiningAreaUpdate,
    RestaurantDocumentCreate,
    RestaurantTableCreate,
    RestaurantTableUpdate,
)
from app.services.operations_service import (
    BusinessSettingsService,
    DepartmentService,
    DiningAreaService,
    OpsDashboardService,
    RestaurantDocumentService,
    RestaurantTableService,
)

dining_router = APIRouter(prefix="/dining-areas", tags=["dining-areas"])
tables_router = APIRouter(prefix="/tables", tags=["tables"])
departments_router = APIRouter(prefix="/departments", tags=["departments"])
settings_router = APIRouter(prefix="/business-settings", tags=["business-settings"])
documents_router = APIRouter(prefix="/restaurant-documents", tags=["restaurant-documents"])
ops_router = APIRouter(prefix="/ops", tags=["operations"])


@dining_router.get("")
def list_dining_areas(
    branch_id: UUID | None = Query(default=None),
    restaurant_id: UUID | None = Query(default=None),
    search: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    active_only: bool = Query(default=False),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = DiningAreaService(db).list_areas(
        branch_id=branch_id,
        restaurant_id=restaurant_id,
        search=search,
        skip=skip,
        limit=limit,
        active_only=active_only,
    )
    return {
        "success": True,
        "message": "Dining areas fetched",
        "data": [i.model_dump(mode="json") for i in data],
    }


@dining_router.post("")
def create_dining_area(
    payload: DiningAreaCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    item = DiningAreaService(db).create(payload, actor_id=user.id)
    return {"success": True, "message": "Dining area created", "data": item.model_dump(mode="json")}


@dining_router.put("/{area_id}")
def update_dining_area(
    area_id: UUID,
    payload: DiningAreaUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    item = DiningAreaService(db).update(area_id, payload, actor_id=user.id)
    return {"success": True, "message": "Dining area updated", "data": item.model_dump(mode="json")}


@dining_router.delete("/{area_id}")
def delete_dining_area(
    area_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    DiningAreaService(db).delete(area_id, actor_id=user.id)
    return {"success": True, "message": "Dining area deleted", "data": None}


@tables_router.get("")
def list_tables(
    branch_id: UUID | None = Query(default=None),
    dining_area_id: UUID | None = Query(default=None),
    restaurant_id: UUID | None = Query(default=None),
    status: TableStatus | None = Query(default=None),
    search: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    active_only: bool = Query(default=False),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = RestaurantTableService(db).list_tables(
        branch_id=branch_id,
        dining_area_id=dining_area_id,
        restaurant_id=restaurant_id,
        status=status,
        search=search,
        skip=skip,
        limit=limit,
        active_only=active_only,
    )
    return {
        "success": True,
        "message": "Tables fetched",
        "data": [i.model_dump(mode="json") for i in data],
    }


@tables_router.post("")
def create_table(
    payload: RestaurantTableCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    item = RestaurantTableService(db).create(payload, actor_id=user.id)
    return {"success": True, "message": "Table created", "data": item.model_dump(mode="json")}


@tables_router.put("/{table_id}")
def update_table(
    table_id: UUID,
    payload: RestaurantTableUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    item = RestaurantTableService(db).update(table_id, payload, actor_id=user.id)
    return {"success": True, "message": "Table updated", "data": item.model_dump(mode="json")}


@tables_router.delete("/{table_id}")
def delete_table(
    table_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    RestaurantTableService(db).delete(table_id, actor_id=user.id)
    return {"success": True, "message": "Table deleted", "data": None}


@tables_router.post("/bulk-delete")
def bulk_delete_tables(
    ids: list[UUID],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    count = RestaurantTableService(db).bulk_delete(ids, actor_id=user.id)
    return {"success": True, "message": f"Deleted {count} tables", "data": {"count": count}}


@departments_router.get("")
def list_departments(
    branch_id: UUID | None = Query(default=None),
    restaurant_id: UUID | None = Query(default=None),
    search: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    active_only: bool = Query(default=False),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = DepartmentService(db).list_departments(
        branch_id=branch_id,
        restaurant_id=restaurant_id,
        search=search,
        skip=skip,
        limit=limit,
        active_only=active_only,
    )
    return {
        "success": True,
        "message": "Departments fetched",
        "data": [i.model_dump(mode="json") for i in data],
    }


@departments_router.post("")
def create_department(
    payload: DepartmentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    item = DepartmentService(db).create(payload, actor_id=user.id)
    return {"success": True, "message": "Department created", "data": item.model_dump(mode="json")}


@departments_router.put("/{dept_id}")
def update_department(
    dept_id: UUID,
    payload: DepartmentUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    item = DepartmentService(db).update(dept_id, payload, actor_id=user.id)
    return {"success": True, "message": "Department updated", "data": item.model_dump(mode="json")}


@departments_router.delete("/{dept_id}")
def delete_department(
    dept_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    DepartmentService(db).delete(dept_id, actor_id=user.id)
    return {"success": True, "message": "Department deleted", "data": None}


@settings_router.get("/{restaurant_id}")
def get_business_settings(
    restaurant_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    item = BusinessSettingsService(db).get_or_default(restaurant_id)
    return {"success": True, "message": "Business settings", "data": item.model_dump(mode="json")}


@settings_router.put("/{restaurant_id}")
def upsert_business_settings(
    restaurant_id: UUID,
    payload: BusinessSettingsUpsert,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    item = BusinessSettingsService(db).upsert(restaurant_id, payload, actor_id=user.id)
    return {"success": True, "message": "Business settings saved", "data": item.model_dump(mode="json")}


@documents_router.get("")
def list_documents(
    restaurant_id: UUID | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = RestaurantDocumentService(db).list_documents(
        restaurant_id=restaurant_id, skip=skip, limit=limit
    )
    return {
        "success": True,
        "message": "Documents fetched",
        "data": [i.model_dump(mode="json") for i in data],
    }


@documents_router.post("")
def create_document_metadata(
    payload: RestaurantDocumentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """Register document metadata (file uploaded to storage; URL stored in PostgreSQL)."""
    item = RestaurantDocumentService(db).create(payload, actor_id=user.id)
    return {"success": True, "message": "Document registered", "data": item.model_dump(mode="json")}


@documents_router.post("/upload")
async def upload_document(
    restaurant_id: UUID = Form(...),
    title: str = Form(...),
    document_type: DocumentType = Form(DocumentType.OTHER),
    notes: str | None = Form(default=None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """Store file under Backend/uploads and persist metadata in PostgreSQL."""
    from pathlib import Path
    import uuid as uuid_lib

    upload_root = Path(__file__).resolve().parents[2] / "uploads" / "documents" / str(restaurant_id)
    upload_root.mkdir(parents=True, exist_ok=True)
    safe_name = file.filename or "document.bin"
    stored = f"{uuid_lib.uuid4().hex}_{safe_name}"
    dest = upload_root / stored
    content = await file.read()
    dest.write_bytes(content)
    file_url = f"/uploads/documents/{restaurant_id}/{stored}"
    payload = RestaurantDocumentCreate(
        restaurant_id=restaurant_id,
        document_type=document_type,
        title=title,
        file_name=safe_name,
        file_url=file_url,
        mime_type=file.content_type,
        file_size=len(content),
        notes=notes,
    )
    item = RestaurantDocumentService(db).create(payload, actor_id=user.id)
    return {"success": True, "message": "Document uploaded", "data": item.model_dump(mode="json")}


@documents_router.delete("/{doc_id}")
def delete_document(
    doc_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    RestaurantDocumentService(db).delete(doc_id, actor_id=user.id)
    return {"success": True, "message": "Document deleted", "data": None}


@ops_router.get("/dashboard")
def ops_dashboard(
    restaurant_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = OpsDashboardService(db).stats(restaurant_id)
    return {"success": True, "message": "Operations dashboard", "data": data.model_dump(mode="json")}
