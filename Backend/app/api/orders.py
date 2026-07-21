"""Orders + POS payment / kitchen / floor / live APIs."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models import User
from app.realtime.ops_hub import ops_hub
from app.schemas.operations import TableMergeIn, TableSplitIn
from app.schemas.order import OrderCreate, OrderItemKitchenUpdate, OrderUpdate, PaymentIn
from app.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])
pos_router = APIRouter(prefix="/pos", tags=["pos"])


@router.get("")
def list_orders(
    branch_id: UUID | None = Query(default=None),
    restaurant_id: UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    search: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = OrderService(db).list_orders(
        branch_id=branch_id,
        restaurant_id=restaurant_id,
        status=status,
        search=search,
        skip=skip,
        limit=limit,
    )
    return {
        "success": True,
        "message": "Orders fetched",
        "data": [item.model_dump(mode="json") for item in data],
    }


@router.get("/{order_id}")
def get_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    item = OrderService(db).get_order(order_id)
    return {"success": True, "message": "Order fetched", "data": item.model_dump(mode="json")}


@router.post("")
def create_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    item = OrderService(db).create_order(payload, actor_id=user.id)
    return {"success": True, "message": "Order created", "data": item.model_dump(mode="json")}


@router.put("/{order_id}")
def update_order(
    order_id: UUID,
    payload: OrderUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    item = OrderService(db).update_order(order_id, payload, actor_id=user.id)
    return {"success": True, "message": "Order updated", "data": item.model_dump(mode="json")}


@router.post("/{order_id}/pay")
def pay_order(
    order_id: UUID,
    payload: PaymentIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    item = OrderService(db).pay_order(order_id, payload, actor_id=user.id)
    return {"success": True, "message": "Payment recorded", "data": item.model_dump(mode="json")}


@router.post("/{order_id}/refund")
def refund_order(
    order_id: UUID,
    payment_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    item = OrderService(db).refund_payment(order_id, payment_id=payment_id, actor_id=user.id)
    return {"success": True, "message": "Refund issued", "data": item.model_dump(mode="json")}


@router.get("/{order_id}/invoice")
def get_invoice(
    order_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = OrderService(db).invoice_payload(order_id)
    return {"success": True, "message": "Invoice", "data": data}


@router.patch("/{order_id}/items/{item_id}/kitchen")
def update_kitchen_item(
    order_id: UUID,
    item_id: UUID,
    payload: OrderItemKitchenUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    item = OrderService(db).update_item_kitchen(
        order_id, item_id, payload.kitchen_status, actor_id=user.id
    )
    return {"success": True, "message": "Kitchen status updated", "data": item.model_dump(mode="json")}


@router.delete("/{order_id}")
def delete_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    OrderService(db).delete_order(order_id, actor_id=user.id)
    return {"success": True, "message": "Order deleted", "data": None}


@pos_router.get("/dashboard")
def pos_dashboard(
    restaurant_id: UUID | None = Query(default=None),
    branch_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = OrderService(db).pos_dashboard(restaurant_id=restaurant_id, branch_id=branch_id)
    return {"success": True, "message": "POS dashboard", "data": data}


@pos_router.get("/kitchen")
def kitchen_board(
    branch_id: UUID | None = Query(default=None),
    restaurant_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = OrderService(db).kitchen_queue(branch_id=branch_id, restaurant_id=restaurant_id)
    return {"success": True, "message": "Kitchen queue", "data": data}


@pos_router.get("/floor")
def floor_plan(
    branch_id: UUID = Query(...),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = OrderService(db).floor_plan(branch_id=branch_id)
    return {"success": True, "message": "Floor plan", "data": data}


@pos_router.patch("/tables/{table_id}/position")
def move_table(
    table_id: UUID,
    pos_x: int = Query(...),
    pos_y: int = Query(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    data = OrderService(db).update_table_position(table_id, pos_x=pos_x, pos_y=pos_y, actor_id=user.id)
    return {"success": True, "message": "Table moved", "data": data}


@pos_router.post("/tables/merge")
def merge_tables(
    payload: TableMergeIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    data = OrderService(db).merge_tables(
        primary_table_id=payload.primary_table_id,
        secondary_table_ids=payload.secondary_table_ids,
        actor_id=user.id,
    )
    return {"success": True, "message": "Tables merged", "data": data}


@pos_router.post("/tables/split")
def split_tables(
    payload: TableSplitIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    data = OrderService(db).split_tables(primary_table_id=payload.primary_table_id, actor_id=user.id)
    return {"success": True, "message": "Tables split", "data": data}


@pos_router.websocket("/ws")
async def pos_websocket(websocket: WebSocket) -> None:
    await ops_hub.connect(websocket)
    try:
        while True:
            # Keepalive / client pings; ignore payload content
            await websocket.receive_text()
    except WebSocketDisconnect:
        await ops_hub.disconnect(websocket)
    except Exception:
        await ops_hub.disconnect(websocket)
