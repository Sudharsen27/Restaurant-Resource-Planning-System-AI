"""Business Intelligence analytics — real PostgreSQL aggregations."""

from __future__ import annotations

import csv
import io
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.models.analytics_bi import AnalyticsAlert, AnalyticsInsight
from app.models.crm_hrms import AttendanceRecord, Payslip, PayrollRun
from app.models.enterprise import (
    Branch,
    Customer,
    Employee,
    InventoryItem,
    InventoryTransaction,
    MenuItem,
    Order,
    OrderItem,
    Payment,
    Product,
    Recipe,
    RestaurantTable,
)
from app.models.enums import (
    AttendanceStatus,
    InventoryTransactionType,
    NotificationType,
    OrderStatus,
    PaymentStatus,
    PayrollStatus,
)
from app.services.notification_service import NotificationService

_REVENUE_STATUSES = {
    OrderStatus.COMPLETED,
    OrderStatus.SERVED,
    OrderStatus.READY,
    OrderStatus.PREPARING,
    OrderStatus.CONFIRMED,
    OrderStatus.PENDING,
}
_PRESENT_STATUSES = {
    AttendanceStatus.PRESENT,
    AttendanceStatus.LATE,
    AttendanceStatus.EARLY_LEAVE,
    AttendanceStatus.HALF_DAY,
}


def _dec(v: Any) -> Decimal:
    return Decimal(str(v or 0))


def _flt(v: Any) -> float:
    if v is None:
        return 0.0
    if isinstance(v, Decimal):
        return float(v)
    return float(v)


def _insight_out(row: AnalyticsInsight) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "restaurant_id": str(row.restaurant_id) if row.restaurant_id else None,
        "branch_id": str(row.branch_id) if row.branch_id else None,
        "severity": row.severity,
        "title": row.title,
        "body": row.body,
        "metric_key": row.metric_key,
        "metric_value": _flt(row.metric_value),
        "payload": row.payload,
        "acknowledged": row.acknowledged,
        "acknowledged_at": row.acknowledged_at.isoformat() if row.acknowledged_at else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def _alert_out(row: AnalyticsAlert) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "restaurant_id": str(row.restaurant_id) if row.restaurant_id else None,
        "branch_id": str(row.branch_id) if row.branch_id else None,
        "alert_type": row.alert_type,
        "severity": row.severity,
        "title": row.title,
        "body": row.body,
        "is_resolved": row.is_resolved,
        "resolved_at": row.resolved_at.isoformat() if row.resolved_at else None,
        "payload": row.payload,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


class AnalyticsBIService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _resolve_range(
        self,
        start: date | datetime | None,
        end: date | datetime | None,
        *,
        default_days: int = 30,
    ) -> tuple[datetime, datetime]:
        now = datetime.now(timezone.utc)
        if end is None:
            end_dt = now
        elif isinstance(end, date) and not isinstance(end, datetime):
            end_dt = datetime.combine(end, datetime.max.time(), tzinfo=timezone.utc)
        else:
            end_dt = end if end.tzinfo else end.replace(tzinfo=timezone.utc)

        if start is None:
            start_dt = end_dt - timedelta(days=default_days)
        elif isinstance(start, date) and not isinstance(start, datetime):
            start_dt = datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc)
        else:
            start_dt = start if start.tzinfo else start.replace(tzinfo=timezone.utc)

        if start_dt >= end_dt:
            start_dt = end_dt - timedelta(days=1)
        return start_dt, end_dt

    def _prior_range(self, start: datetime, end: datetime) -> tuple[datetime, datetime]:
        span = end - start
        prior_end = start
        prior_start = start - span
        return prior_start, prior_end

    def _order_base(
        self,
        *,
        restaurant_id: UUID | None = None,
        branch_id: UUID | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        include_cancelled: bool = False,
    ):
        stmt = select(Order).where(Order.is_deleted.is_(False))
        if not include_cancelled:
            stmt = stmt.where(Order.status != OrderStatus.CANCELLED)
        if branch_id is not None:
            stmt = stmt.where(Order.branch_id == branch_id)
        elif restaurant_id is not None:
            stmt = stmt.join(Branch, Branch.id == Order.branch_id).where(
                Branch.restaurant_id == restaurant_id
            )
        if start is not None:
            stmt = stmt.where(Order.order_date >= start)
        if end is not None:
            stmt = stmt.where(Order.order_date <= end)
        return stmt

    def _sum_revenue(
        self,
        *,
        restaurant_id: UUID | None,
        branch_id: UUID | None,
        start: datetime,
        end: datetime,
    ) -> Decimal:
        stmt = (
            select(func.coalesce(func.sum(Order.total), 0))
            .select_from(Order)
            .where(
                Order.is_deleted.is_(False),
                Order.status != OrderStatus.CANCELLED,
                Order.order_date >= start,
                Order.order_date <= end,
            )
        )
        if branch_id is not None:
            stmt = stmt.where(Order.branch_id == branch_id)
        elif restaurant_id is not None:
            stmt = stmt.join(Branch, Branch.id == Order.branch_id).where(
                Branch.restaurant_id == restaurant_id
            )
        return _dec(self.db.scalar(stmt))

    def _count_orders(
        self,
        *,
        restaurant_id: UUID | None,
        branch_id: UUID | None,
        start: datetime,
        end: datetime,
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(Order)
            .where(
                Order.is_deleted.is_(False),
                Order.status != OrderStatus.CANCELLED,
                Order.order_date >= start,
                Order.order_date <= end,
            )
        )
        if branch_id is not None:
            stmt = stmt.where(Order.branch_id == branch_id)
        elif restaurant_id is not None:
            stmt = stmt.join(Branch, Branch.id == Order.branch_id).where(
                Branch.restaurant_id == restaurant_id
            )
        return int(self.db.scalar(stmt) or 0)

    def _inventory_value(
        self,
        *,
        restaurant_id: UUID | None,
        branch_id: UUID | None,
    ) -> Decimal:
        stmt = (
            select(
                func.coalesce(
                    func.sum(InventoryItem.quantity_on_hand * Product.unit_cost),
                    0,
                )
            )
            .select_from(InventoryItem)
            .join(Product, Product.id == InventoryItem.product_id)
            .where(InventoryItem.is_deleted.is_(False), Product.is_deleted.is_(False))
        )
        if branch_id is not None:
            stmt = stmt.where(InventoryItem.branch_id == branch_id)
        elif restaurant_id is not None:
            stmt = stmt.join(Branch, Branch.id == InventoryItem.branch_id).where(
                Branch.restaurant_id == restaurant_id
            )
        return _dec(self.db.scalar(stmt))

    def _food_cost_from_txns(
        self,
        *,
        restaurant_id: UUID | None,
        branch_id: UUID | None,
        start: datetime,
        end: datetime,
    ) -> Decimal:
        cost_expr = func.abs(InventoryTransaction.quantity) * func.coalesce(
            InventoryTransaction.unit_cost, Product.unit_cost, 0
        )
        stmt = (
            select(func.coalesce(func.sum(cost_expr), 0))
            .select_from(InventoryTransaction)
            .join(InventoryItem, InventoryItem.id == InventoryTransaction.inventory_item_id)
            .join(Product, Product.id == InventoryItem.product_id)
            .where(
                InventoryTransaction.is_deleted.is_(False),
                InventoryTransaction.transaction_type == InventoryTransactionType.SALE,
                InventoryTransaction.created_at >= start,
                InventoryTransaction.created_at <= end,
            )
        )
        if branch_id is not None:
            stmt = stmt.where(InventoryItem.branch_id == branch_id)
        elif restaurant_id is not None:
            stmt = stmt.join(Branch, Branch.id == InventoryItem.branch_id).where(
                Branch.restaurant_id == restaurant_id
            )
        txn_cost = _dec(self.db.scalar(stmt))
        if txn_cost > 0:
            return txn_cost

        # Recipe-based fallback from order items in range
        item_stmt = (
            select(
                OrderItem.menu_item_id,
                func.sum(OrderItem.quantity).label("qty"),
            )
            .join(Order, Order.id == OrderItem.order_id)
            .where(
                Order.is_deleted.is_(False),
                Order.status != OrderStatus.CANCELLED,
                Order.order_date >= start,
                Order.order_date <= end,
                OrderItem.is_deleted.is_(False),
            )
            .group_by(OrderItem.menu_item_id)
        )
        if branch_id is not None:
            item_stmt = item_stmt.where(Order.branch_id == branch_id)
        elif restaurant_id is not None:
            item_stmt = item_stmt.join(Branch, Branch.id == Order.branch_id).where(
                Branch.restaurant_id == restaurant_id
            )
        rows = self.db.execute(item_stmt).all()
        total = Decimal("0")
        for menu_item_id, qty in rows:
            if menu_item_id is None:
                continue
            portion = self._menu_item_portion_cost(menu_item_id)
            total += portion * _dec(qty)
        return total

    def _menu_item_portion_cost(self, menu_item_id: UUID) -> Decimal:
        recipe = self.db.scalars(
            select(Recipe).where(
                Recipe.menu_item_id == menu_item_id,
                Recipe.is_deleted.is_(False),
            )
        ).first()
        if not recipe:
            item = self.db.get(MenuItem, menu_item_id)
            if item and item.product_id:
                prod = self.db.get(Product, item.product_id)
                return _dec(prod.unit_cost) if prod else Decimal("0")
            return Decimal("0")
        yield_p = _dec(recipe.yield_portions) or Decimal("1")
        ing_cost = Decimal("0")
        for ing in recipe.ingredients:
            if ing.is_deleted:
                continue
            prod = self.db.get(Product, ing.product_id)
            if prod:
                waste = Decimal("1") + _dec(ing.waste_percent) / Decimal("100")
                ing_cost += _dec(ing.quantity) * _dec(prod.unit_cost) * waste
        return (ing_cost / yield_p).quantize(Decimal("0.01"))

    def _labor_cost(
        self,
        *,
        restaurant_id: UUID | None,
        branch_id: UUID | None,
        start: datetime,
        end: datetime,
    ) -> Decimal:
        start_d = start.date()
        end_d = end.date()

        # Payslip net for payroll periods overlapping the range
        if restaurant_id is not None:
            runs = self.db.scalars(
                select(PayrollRun).where(
                    PayrollRun.restaurant_id == restaurant_id,
                    PayrollRun.is_deleted.is_(False),
                    PayrollRun.status.in_(
                        [PayrollStatus.GENERATED, PayrollStatus.LOCKED, PayrollStatus.PAID]
                    ),
                )
            ).all()
            payslip_total = Decimal("0")
            for run in runs:
                period_start = date(run.period_year, run.period_month, 1)
                last_day = (
                    date(run.period_year, run.period_month, 28)
                    + timedelta(days=4)
                ).replace(day=1) - timedelta(days=1)
                period_end = last_day
                if period_end < start_d or period_start > end_d:
                    continue
                slip_stmt = (
                    select(func.coalesce(func.sum(Payslip.net_salary), 0))
                    .select_from(Payslip)
                    .join(Employee, Employee.id == Payslip.employee_id)
                    .where(
                        Payslip.payroll_run_id == run.id,
                        Payslip.is_deleted.is_(False),
                    )
                )
                if branch_id is not None:
                    slip_stmt = slip_stmt.where(Employee.branch_id == branch_id)
                payslip_total += _dec(self.db.scalar(slip_stmt))
            if payslip_total > 0:
                return payslip_total

        # Attendance × hourly wage fallback
        att_stmt = (
            select(AttendanceRecord, Employee)
            .join(Employee, Employee.id == AttendanceRecord.employee_id)
            .where(
                AttendanceRecord.is_deleted.is_(False),
                AttendanceRecord.work_date >= start_d,
                AttendanceRecord.work_date <= end_d,
                AttendanceRecord.status.in_(_PRESENT_STATUSES),
            )
        )
        if branch_id is not None:
            att_stmt = att_stmt.where(AttendanceRecord.branch_id == branch_id)
        elif restaurant_id is not None:
            att_stmt = att_stmt.join(Branch, Branch.id == AttendanceRecord.branch_id).where(
                Branch.restaurant_id == restaurant_id
            )
        total = Decimal("0")
        for att, emp in self.db.execute(att_stmt).all():
            hours = self._attendance_hours(att)
            wage = _dec(emp.hourly_wage)
            if wage <= 0 and _dec(emp.monthly_salary) > 0:
                wage = _dec(emp.monthly_salary) / Decimal("160")
            total += hours * wage
        return total.quantize(Decimal("0.01"))

    def _attendance_hours(self, att: AttendanceRecord) -> Decimal:
        if att.clock_in and att.clock_out:
            delta = att.clock_out - att.clock_in
            if att.break_start and att.break_end:
                break_mins = (att.break_end - att.break_start).total_seconds() / 60
                mins = max(delta.total_seconds() / 60 - break_mins, 0)
            else:
                mins = max(delta.total_seconds() / 60, 0)
            ot = _dec(att.overtime_minutes) / Decimal("60")
            return _dec(mins) / Decimal("60") + ot
        if att.status == AttendanceStatus.HALF_DAY:
            return Decimal("4")
        return Decimal("8")

    def _customer_counts(
        self,
        *,
        restaurant_id: UUID | None,
        branch_id: UUID | None,
        start: datetime,
        end: datetime,
    ) -> tuple[int, int, float]:
        order_stmt = (
            select(Order.customer_id, func.min(Order.order_date).label("first_order"))
            .where(
                Order.is_deleted.is_(False),
                Order.status != OrderStatus.CANCELLED,
                Order.customer_id.isnot(None),
                Order.order_date <= end,
            )
            .group_by(Order.customer_id)
        )
        if branch_id is not None:
            order_stmt = order_stmt.where(Order.branch_id == branch_id)
        elif restaurant_id is not None:
            order_stmt = order_stmt.join(Branch, Branch.id == Order.branch_id).where(
                Branch.restaurant_id == restaurant_id
            )
        all_customers = self.db.execute(order_stmt).all()

        in_range_stmt = (
            select(Order.customer_id)
            .where(
                Order.is_deleted.is_(False),
                Order.status != OrderStatus.CANCELLED,
                Order.customer_id.isnot(None),
                Order.order_date >= start,
                Order.order_date <= end,
            )
            .distinct()
        )
        if branch_id is not None:
            in_range_stmt = in_range_stmt.where(Order.branch_id == branch_id)
        elif restaurant_id is not None:
            in_range_stmt = in_range_stmt.join(Branch, Branch.id == Order.branch_id).where(
                Branch.restaurant_id == restaurant_id
            )
        in_range_ids = {row[0] for row in self.db.execute(in_range_stmt).all() if row[0]}
        if not in_range_ids:
            return 0, 0, 0.0

        first_map = {cid: first for cid, first in all_customers if cid}
        new_count = sum(
            1 for cid in in_range_ids if cid in first_map and start <= first_map[cid] <= end
        )
        repeat_count = len(in_range_ids) - new_count
        retention = repeat_count / len(in_range_ids) if in_range_ids else 0.0
        return repeat_count, new_count, retention

    # ── Public API ───────────────────────────────────────────────────────────

    def executive_kpis(
        self,
        restaurant_id: UUID | None = None,
        branch_id: UUID | None = None,
        start: date | datetime | None = None,
        end: date | datetime | None = None,
    ) -> dict[str, Any]:
        start_dt, end_dt = self._resolve_range(start, end)
        prior_start, prior_end = self._prior_range(start_dt, end_dt)

        revenue = self._sum_revenue(
            restaurant_id=restaurant_id,
            branch_id=branch_id,
            start=start_dt,
            end=end_dt,
        )
        prior_revenue = self._sum_revenue(
            restaurant_id=restaurant_id,
            branch_id=branch_id,
            start=prior_start,
            end=prior_end,
        )
        orders_count = self._count_orders(
            restaurant_id=restaurant_id,
            branch_id=branch_id,
            start=start_dt,
            end=end_dt,
        )
        aov = (revenue / orders_count).quantize(Decimal("0.01")) if orders_count else Decimal("0")
        growth_pct = (
            float((revenue - prior_revenue) / prior_revenue * 100) if prior_revenue > 0 else 0.0
        )

        inventory_value = self._inventory_value(restaurant_id=restaurant_id, branch_id=branch_id)
        food_cost = self._food_cost_from_txns(
            restaurant_id=restaurant_id,
            branch_id=branch_id,
            start=start_dt,
            end=end_dt,
        )
        food_cost_pct = float(food_cost / revenue * 100) if revenue > 0 else 0.0
        labor_cost = self._labor_cost(
            restaurant_id=restaurant_id,
            branch_id=branch_id,
            start=start_dt,
            end=end_dt,
        )
        profit = revenue - food_cost - labor_cost
        repeat_customers, new_customers, retention = self._customer_counts(
            restaurant_id=restaurant_id,
            branch_id=branch_id,
            start=start_dt,
            end=end_dt,
        )

        return {
            "period_start": start_dt.isoformat(),
            "period_end": end_dt.isoformat(),
            "revenue": _flt(revenue),
            "prior_revenue": _flt(prior_revenue),
            "growth_pct": round(growth_pct, 2),
            "orders_count": orders_count,
            "aov": _flt(aov),
            "inventory_value": _flt(inventory_value),
            "food_cost": _flt(food_cost),
            "food_cost_pct": round(food_cost_pct, 2),
            "labor_cost": _flt(labor_cost),
            "profit": _flt(profit),
            "customer_retention": round(retention, 4),
            "repeat_customers": repeat_customers,
            "new_customers": new_customers,
        }

    def revenue_trend(
        self,
        *,
        restaurant_id: UUID | None = None,
        branch_id: UUID | None = None,
        start: date | datetime | None = None,
        end: date | datetime | None = None,
        days: int = 30,
    ) -> list[dict[str, Any]]:
        if start is None and end is None:
            end_dt = datetime.now(timezone.utc)
            start_dt = end_dt - timedelta(days=days)
        else:
            start_dt, end_dt = self._resolve_range(start, end, default_days=days)

        stmt = (
            select(
                func.date_trunc("day", Order.order_date).label("day"),
                func.coalesce(func.sum(Order.total), 0).label("revenue"),
                func.count(Order.id).label("orders"),
            )
            .where(
                Order.is_deleted.is_(False),
                Order.status != OrderStatus.CANCELLED,
                Order.order_date >= start_dt,
                Order.order_date <= end_dt,
            )
            .group_by(func.date_trunc("day", Order.order_date))
            .order_by(func.date_trunc("day", Order.order_date))
        )
        if branch_id is not None:
            stmt = stmt.where(Order.branch_id == branch_id)
        elif restaurant_id is not None:
            stmt = stmt.join(Branch, Branch.id == Order.branch_id).where(
                Branch.restaurant_id == restaurant_id
            )

        by_day: dict[str, dict] = {}
        for day, rev, cnt in self.db.execute(stmt).all():
            key = day.date().isoformat() if hasattr(day, "date") else str(day)[:10]
            by_day[key] = {"date": key, "revenue": _flt(rev), "orders": int(cnt or 0)}

        series: list[dict] = []
        cursor = start_dt.date()
        end_date = end_dt.date()
        while cursor <= end_date:
            key = cursor.isoformat()
            row = by_day.get(key, {"date": key, "revenue": 0.0, "orders": 0})
            series.append(row)
            cursor += timedelta(days=1)
        return series

    def payment_distribution(
        self,
        *,
        restaurant_id: UUID | None = None,
        branch_id: UUID | None = None,
        start: date | datetime | None = None,
        end: date | datetime | None = None,
    ) -> list[dict[str, Any]]:
        start_dt, end_dt = self._resolve_range(start, end)
        stmt = (
            select(
                Payment.method,
                func.coalesce(func.sum(Payment.amount), 0).label("amount"),
                func.count(Payment.id).label("count"),
            )
            .join(Order, Order.id == Payment.order_id)
            .where(
                Payment.is_deleted.is_(False),
                Payment.status.in_([PaymentStatus.PAID, PaymentStatus.PARTIAL]),
                Order.is_deleted.is_(False),
                Order.order_date >= start_dt,
                Order.order_date <= end_dt,
            )
            .group_by(Payment.method)
        )
        if branch_id is not None:
            stmt = stmt.where(Order.branch_id == branch_id)
        elif restaurant_id is not None:
            stmt = stmt.join(Branch, Branch.id == Order.branch_id).where(
                Branch.restaurant_id == restaurant_id
            )
        rows = self.db.execute(stmt).all()
        total = sum(_dec(amt) for _, amt, _ in rows) or Decimal("1")
        return [
            {
                "method": m.value if hasattr(m, "value") else str(m),
                "amount": _flt(amt),
                "count": int(cnt or 0),
                "pct": round(_flt(amt / total * 100), 2),
            }
            for m, amt, cnt in rows
        ]

    def menu_analytics(
        self,
        *,
        restaurant_id: UUID | None = None,
        branch_id: UUID | None = None,
        start: date | datetime | None = None,
        end: date | datetime | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        start_dt, end_dt = self._resolve_range(start, end)
        stmt = (
            select(
                OrderItem.menu_item_id,
                OrderItem.item_name,
                func.sum(OrderItem.quantity).label("qty"),
                func.sum(OrderItem.line_total).label("revenue"),
            )
            .join(Order, Order.id == OrderItem.order_id)
            .where(
                OrderItem.is_deleted.is_(False),
                Order.is_deleted.is_(False),
                Order.status != OrderStatus.CANCELLED,
                Order.order_date >= start_dt,
                Order.order_date <= end_dt,
            )
            .group_by(OrderItem.menu_item_id, OrderItem.item_name)
        )
        if branch_id is not None:
            stmt = stmt.where(Order.branch_id == branch_id)
        elif restaurant_id is not None:
            stmt = stmt.join(Branch, Branch.id == Order.branch_id).where(
                Branch.restaurant_id == restaurant_id
            )

        items: list[dict] = []
        for menu_item_id, name, qty, rev in self.db.execute(stmt).all():
            portion_cost = self._menu_item_portion_cost(menu_item_id) if menu_item_id else Decimal("0")
            menu_item = self.db.get(MenuItem, menu_item_id) if menu_item_id else None
            price = _dec(menu_item.price) if menu_item else Decimal("0")
            margin = price - portion_cost
            margin_pct = float(margin / price * 100) if price > 0 else 0.0
            items.append(
                {
                    "menu_item_id": str(menu_item_id) if menu_item_id else None,
                    "name": name,
                    "quantity_sold": _flt(qty),
                    "revenue": _flt(rev),
                    "unit_price": _flt(price),
                    "food_cost_per_portion": _flt(portion_cost),
                    "margin": _flt(margin),
                    "margin_pct": round(margin_pct, 2),
                }
            )

        by_qty = sorted(items, key=lambda x: x["quantity_sold"], reverse=True)
        by_rev = sorted(items, key=lambda x: x["revenue"], reverse=True)
        by_margin = sorted(items, key=lambda x: x["margin_pct"], reverse=True)

        return {
            "best_sellers_qty": by_qty[:limit],
            "best_sellers_revenue": by_rev[:limit],
            "worst_sellers_qty": sorted(items, key=lambda x: x["quantity_sold"])[:limit],
            "highest_margin": by_margin[:limit],
            "lowest_margin": sorted(items, key=lambda x: x["margin_pct"])[:limit],
            "total_items_tracked": len(items),
        }

    def customer_analytics(
        self,
        *,
        restaurant_id: UUID | None = None,
        branch_id: UUID | None = None,
        start: date | datetime | None = None,
        end: date | datetime | None = None,
    ) -> dict[str, Any]:
        start_dt, end_dt = self._resolve_range(start, end)
        repeat, new, retention = self._customer_counts(
            restaurant_id=restaurant_id,
            branch_id=branch_id,
            start=start_dt,
            end=end_dt,
        )

        cust_stmt = select(Customer).where(Customer.is_deleted.is_(False))
        if restaurant_id is not None:
            cust_stmt = cust_stmt.where(Customer.restaurant_id == restaurant_id)
        customers = list(self.db.scalars(cust_stmt).all())

        vip_count = sum(1 for c in customers if c.is_vip)
        loyalty_sum = sum(c.loyalty_points for c in customers)
        loyalty_avg = loyalty_sum / len(customers) if customers else 0
        clv_avg = (
            sum(_dec(c.lifetime_spend) for c in customers) / len(customers) if customers else Decimal("0")
        )
        visit_avg = sum(c.visit_count for c in customers) / len(customers) if customers else 0

        segments: dict[str, int] = defaultdict(int)
        for c in customers:
            level = c.membership_level.value if hasattr(c.membership_level, "value") else str(c.membership_level)
            segments[level] += 1

        return {
            "new_customers": new,
            "returning_customers": repeat,
            "retention_rate": round(retention, 4),
            "vip_count": vip_count,
            "total_customers": len(customers),
            "loyalty_points_sum": loyalty_sum,
            "loyalty_points_avg": round(loyalty_avg, 2),
            "avg_clv": _flt(clv_avg),
            "avg_visit_count": round(visit_avg, 2),
            "segments_by_membership": dict(segments),
        }

    def employee_analytics(
        self,
        *,
        restaurant_id: UUID | None = None,
        branch_id: UUID | None = None,
        start: date | datetime | None = None,
        end: date | datetime | None = None,
    ) -> dict[str, Any]:
        start_dt, end_dt = self._resolve_range(start, end)
        start_d, end_d = start_dt.date(), end_dt.date()
        work_days = max((end_d - start_d).days + 1, 1)

        emp_stmt = select(Employee).where(Employee.is_deleted.is_(False))
        if branch_id is not None:
            emp_stmt = emp_stmt.where(Employee.branch_id == branch_id)
        elif restaurant_id is not None:
            emp_stmt = emp_stmt.join(Branch, Branch.id == Employee.branch_id).where(
                Branch.restaurant_id == restaurant_id
            )
        employees = list(self.db.scalars(emp_stmt).all())
        emp_ids = [e.id for e in employees]

        att_stmt = select(AttendanceRecord).where(
            AttendanceRecord.is_deleted.is_(False),
            AttendanceRecord.work_date >= start_d,
            AttendanceRecord.work_date <= end_d,
        )
        if emp_ids:
            att_stmt = att_stmt.where(AttendanceRecord.employee_id.in_(emp_ids))
        else:
            att_stmt = att_stmt.where(False)
        records = list(self.db.scalars(att_stmt).all())

        present_days = sum(1 for r in records if r.status in _PRESENT_STATUSES)
        expected_days = len(employees) * work_days if employees else work_days
        attendance_pct = present_days / expected_days * 100 if expected_days else 0.0
        overtime_total = sum(r.overtime_minutes for r in records)

        hours_by_emp: dict[UUID, float] = defaultdict(float)
        for r in records:
            if r.status in _PRESENT_STATUSES:
                hours_by_emp[r.employee_id] += _flt(self._attendance_hours(r))

        ranking = []
        emp_map = {e.id: e for e in employees}
        for eid, hrs in sorted(hours_by_emp.items(), key=lambda x: x[1], reverse=True):
            emp = emp_map.get(eid)
            if emp:
                ranking.append(
                    {
                        "employee_id": str(eid),
                        "name": emp.full_name,
                        "role": emp.role.value if hasattr(emp.role, "value") else str(emp.role),
                        "hours_worked": round(hrs, 2),
                        "overtime_minutes": sum(
                            r.overtime_minutes
                            for r in records
                            if r.employee_id == eid
                        ),
                    }
                )

        # Sales per waiter via table assigned_waiter
        start_dt, end_dt = self._resolve_range(start, end)
        waiter_sales: dict[str, float] = defaultdict(float)
        order_stmt = (
            select(Order, RestaurantTable.assigned_waiter)
            .outerjoin(RestaurantTable, RestaurantTable.id == Order.table_id)
            .where(
                Order.is_deleted.is_(False),
                Order.status != OrderStatus.CANCELLED,
                Order.order_date >= start_dt,
                Order.order_date <= end_dt,
            )
        )
        if branch_id is not None:
            order_stmt = order_stmt.where(Order.branch_id == branch_id)
        elif restaurant_id is not None:
            order_stmt = order_stmt.join(Branch, Branch.id == Order.branch_id).where(
                Branch.restaurant_id == restaurant_id
            )
        for order, waiter in self.db.execute(order_stmt).all():
            if waiter:
                waiter_sales[waiter] += _flt(order.total)

        sales_per_waiter = [
            {"waiter": name, "revenue": round(rev, 2)}
            for name, rev in sorted(waiter_sales.items(), key=lambda x: x[1], reverse=True)
        ]

        return {
            "attendance_pct": round(attendance_pct, 2),
            "overtime_minutes_total": overtime_total,
            "employee_count": len(employees),
            "hours_ranking": ranking[:20],
            "sales_per_waiter": sales_per_waiter,
        }

    def smart_inventory(
        self,
        *,
        restaurant_id: UUID | None = None,
        branch_id: UUID | None = None,
        lookback_days: int = 30,
    ) -> dict[str, Any]:
        inv_stmt = (
            select(InventoryItem, Product)
            .join(Product, Product.id == InventoryItem.product_id)
            .where(InventoryItem.is_deleted.is_(False), Product.is_deleted.is_(False))
        )
        if branch_id is not None:
            inv_stmt = inv_stmt.where(InventoryItem.branch_id == branch_id)
        elif restaurant_id is not None:
            inv_stmt = inv_stmt.join(Branch, Branch.id == InventoryItem.branch_id).where(
                Branch.restaurant_id == restaurant_id
            )
        inv_rows = list(self.db.execute(inv_stmt).all())

        low_stock: list[dict] = []
        for item, product in inv_rows:
            on_hand = _dec(item.quantity_on_hand)
            reorder = _dec(item.reorder_level)
            if on_hand <= reorder:
                suggested = max(reorder * 2 - on_hand, Decimal("0"))
                low_stock.append(
                    {
                        "product_id": str(product.id),
                        "product_name": product.name,
                        "sku": product.sku,
                        "on_hand": _flt(on_hand),
                        "reorder_level": _flt(reorder),
                        "suggested_reorder_qty": _flt(suggested),
                    }
                )

        since = datetime.now(timezone.utc) - timedelta(days=lookback_days)
        sale_stmt = (
            select(
                InventoryTransaction.product_id,
                func.sum(func.abs(InventoryTransaction.quantity)).label("qty"),
            )
            .where(
                InventoryTransaction.is_deleted.is_(False),
                InventoryTransaction.transaction_type == InventoryTransactionType.SALE,
                InventoryTransaction.created_at >= since,
                InventoryTransaction.product_id.isnot(None),
            )
            .group_by(InventoryTransaction.product_id)
        )
        if branch_id is not None:
            sale_stmt = sale_stmt.where(InventoryTransaction.branch_id == branch_id)
        elif restaurant_id is not None:
            sale_stmt = sale_stmt.join(
                InventoryItem, InventoryItem.id == InventoryTransaction.inventory_item_id
            ).join(Branch, Branch.id == InventoryItem.branch_id).where(
                Branch.restaurant_id == restaurant_id
            )
        sale_map = {pid: _flt(qty) for pid, qty in self.db.execute(sale_stmt).all() if pid}

        # Fallback from order items linked products
        if not sale_map:
            oi_stmt = (
                select(
                    MenuItem.product_id,
                    func.sum(OrderItem.quantity).label("qty"),
                )
                .join(Order, Order.id == OrderItem.order_id)
                .join(MenuItem, MenuItem.id == OrderItem.menu_item_id)
                .where(
                    Order.is_deleted.is_(False),
                    Order.status != OrderStatus.CANCELLED,
                    Order.order_date >= since,
                    MenuItem.product_id.isnot(None),
                )
                .group_by(MenuItem.product_id)
            )
            if branch_id is not None:
                oi_stmt = oi_stmt.where(Order.branch_id == branch_id)
            elif restaurant_id is not None:
                oi_stmt = oi_stmt.join(Branch, Branch.id == Order.branch_id).where(
                    Branch.restaurant_id == restaurant_id
                )
            sale_map = {pid: _flt(qty) for pid, qty in self.db.execute(oi_stmt).all() if pid}

        movers: list[dict] = []
        for item, product in inv_rows:
            qty_sold = sale_map.get(product.id, 0.0)
            daily_rate = qty_sold / lookback_days if lookback_days else 0
            movers.append(
                {
                    "product_id": str(product.id),
                    "product_name": product.name,
                    "qty_sold_period": qty_sold,
                    "daily_velocity": round(daily_rate, 4),
                    "on_hand": _flt(item.quantity_on_hand),
                }
            )

        movers_sorted = sorted(movers, key=lambda x: x["qty_sold_period"], reverse=True)
        fast = [m for m in movers_sorted if m["qty_sold_period"] > 0][:10]
        slow = sorted(
            [m for m in movers if m["on_hand"] > 0],
            key=lambda x: x["qty_sold_period"],
        )[:10]
        dead = [m for m in movers if m["qty_sold_period"] == 0 and m["on_hand"] > 0][:10]

        return {
            "low_stock": low_stock,
            "fast_movers": fast,
            "slow_movers": slow,
            "dead_stock": dead,
            "inventory_value": _flt(
                self._inventory_value(restaurant_id=restaurant_id, branch_id=branch_id)
            ),
        }

    def sales_forecast(
        self,
        *,
        restaurant_id: UUID | None = None,
        branch_id: UUID | None = None,
        horizon: str = "week",
    ) -> dict[str, Any]:
        end_dt = datetime.now(timezone.utc)
        start_dt = end_dt - timedelta(days=28)
        series = self.revenue_trend(
            restaurant_id=restaurant_id,
            branch_id=branch_id,
            start=start_dt,
            end=end_dt,
        )
        revenues = [s["revenue"] for s in series]
        window = min(7, len(revenues)) or 1
        sma = sum(revenues[-window:]) / window if revenues else 0.0

        weekday_factors: dict[int, list[float]] = defaultdict(list)
        for s in series:
            d = date.fromisoformat(s["date"])
            if s["revenue"] > 0:
                weekday_factors[d.weekday()].append(s["revenue"])
        avg_by_wd = {
            wd: sum(vals) / len(vals) if vals else sma for wd, vals in weekday_factors.items()
        }
        overall_avg = sum(revenues) / len(revenues) if revenues else 1.0
        wd_multiplier = {
            wd: (avg / overall_avg if overall_avg else 1.0) for wd, avg in avg_by_wd.items()
        }

        horizon_days = {"tomorrow": 1, "week": 7, "month": 30}.get(horizon.lower(), 7)
        predictions: list[dict] = []
        cursor = end_dt.date() + timedelta(days=1)
        for i in range(horizon_days):
            target = cursor + timedelta(days=i)
            factor = wd_multiplier.get(target.weekday(), 1.0)
            pred_rev = round(sma * factor, 2)
            predictions.append({"date": target.isoformat(), "predicted_revenue": pred_rev})

        # Item demand from recent averages
        start_dt2, end_dt2 = self._resolve_range(start_dt, end_dt)
        menu = self.menu_analytics(
            restaurant_id=restaurant_id,
            branch_id=branch_id,
            start=start_dt2,
            end=end_dt2,
            limit=5,
        )
        top_items = menu.get("best_sellers_qty", [])
        daily_item_demand = [
            {
                "name": it["name"],
                "predicted_daily_qty": round(it["quantity_sold"] / 28, 2),
            }
            for it in top_items
        ]

        return {
            "horizon": horizon,
            "method": "7-day SMA with weekday seasonality factor (28-day calibration)",
            "baseline_daily_revenue": round(sma, 2),
            "predictions": predictions,
            "predicted_total_revenue": round(sum(p["predicted_revenue"] for p in predictions), 2),
            "top_item_demand": daily_item_demand,
        }

    def demand_forecast(
        self,
        *,
        restaurant_id: UUID | None = None,
        branch_id: UUID | None = None,
    ) -> dict[str, Any]:
        forecast = self.sales_forecast(
            restaurant_id=restaurant_id, branch_id=branch_id, horizon="week"
        )
        item_demand = {d["name"]: d["predicted_daily_qty"] for d in forecast.get("top_item_demand", [])}

        # Map menu items to ingredients via recipes
        ing_demand: dict[str, float] = defaultdict(float)
        if item_demand:
            menu_stmt = select(MenuItem).where(MenuItem.is_deleted.is_(False))
            if restaurant_id is not None:
                menu_stmt = menu_stmt.where(MenuItem.restaurant_id == restaurant_id)
            for mi in self.db.scalars(menu_stmt).all():
                if mi.name not in item_demand:
                    continue
                qty = item_demand[mi.name]
                recipe = self.db.scalars(
                    select(Recipe).where(Recipe.menu_item_id == mi.id, Recipe.is_deleted.is_(False))
                ).first()
                if not recipe:
                    continue
                yield_p = _dec(recipe.yield_portions) or Decimal("1")
                for ing in recipe.ingredients:
                    if ing.is_deleted:
                        continue
                    prod = self.db.get(Product, ing.product_id)
                    if prod:
                        need = _flt(_dec(ing.quantity) / yield_p * _dec(qty))
                        ing_demand[prod.name] += need

        top_ingredients = [
            {"ingredient": name, "predicted_daily_qty": round(qty, 3)}
            for name, qty in sorted(ing_demand.items(), key=lambda x: x[1], reverse=True)[:15]
        ]

        # Peak hours from last 28 days
        end_dt = datetime.now(timezone.utc)
        start_dt = end_dt - timedelta(days=28)
        hour_stmt = (
            select(
                func.extract("hour", Order.order_date).label("hr"),
                func.count(Order.id).label("cnt"),
            )
            .where(
                Order.is_deleted.is_(False),
                Order.status != OrderStatus.CANCELLED,
                Order.order_date >= start_dt,
                Order.order_date <= end_dt,
            )
            .group_by(func.extract("hour", Order.order_date))
            .order_by(func.count(Order.id).desc())
        )
        if branch_id is not None:
            hour_stmt = hour_stmt.where(Order.branch_id == branch_id)
        elif restaurant_id is not None:
            hour_stmt = hour_stmt.join(Branch, Branch.id == Order.branch_id).where(
                Branch.restaurant_id == restaurant_id
            )
        peak_hours = [
            {"hour": int(hr), "orders": int(cnt)}
            for hr, cnt in self.db.execute(hour_stmt).all()
        ]

        # Footfall
        foot_stmt = (
            select(
                func.count(func.distinct(Order.customer_id)),
                func.coalesce(func.sum(Order.guest_count), 0),
                func.count(Order.id),
            )
            .where(
                Order.is_deleted.is_(False),
                Order.status != OrderStatus.CANCELLED,
                Order.order_date >= start_dt,
                Order.order_date <= end_dt,
            )
        )
        if branch_id is not None:
            foot_stmt = foot_stmt.where(Order.branch_id == branch_id)
        elif restaurant_id is not None:
            foot_stmt = foot_stmt.join(Branch, Branch.id == Order.branch_id).where(
                Branch.restaurant_id == restaurant_id
            )
        unique_cust, guest_sum, order_cnt = self.db.execute(foot_stmt).one()
        days = 28
        avg_footfall = _flt(guest_sum) / days if guest_sum else _flt(unique_cust) / days

        return {
            "top_ingredients": top_ingredients,
            "peak_hours": peak_hours[:8],
            "avg_daily_footfall": round(avg_footfall, 2),
            "unique_customers_28d": int(unique_cust or 0),
            "total_guest_count_28d": int(guest_sum or 0),
            "orders_28d": int(order_cnt or 0),
            "sales_forecast_summary": {
                "predicted_week_revenue": forecast.get("predicted_total_revenue"),
                "method": forecast.get("method"),
            },
        }

    def generate_insights(
        self,
        *,
        restaurant_id: UUID | None = None,
        branch_id: UUID | None = None,
        start: date | datetime | None = None,
        end: date | datetime | None = None,
        actor_id: int | None = None,
        refresh: bool = False,
    ) -> list[dict[str, Any]]:
        if refresh and restaurant_id is not None:
            existing = self.db.scalars(
                select(AnalyticsInsight).where(
                    AnalyticsInsight.restaurant_id == restaurant_id,
                    AnalyticsInsight.is_deleted.is_(False),
                    AnalyticsInsight.acknowledged.is_(False),
                )
            ).all()
            for row in existing:
                if branch_id is None or row.branch_id == branch_id:
                    row.soft_delete()

        kpis = self.executive_kpis(restaurant_id, branch_id, start, end)
        inventory = self.smart_inventory(restaurant_id=restaurant_id, branch_id=branch_id)
        menu = self.menu_analytics(restaurant_id=restaurant_id, branch_id=branch_id, start=start, end=end)

        rules: list[tuple[str, str, str, str | None, float | None, dict | None]] = []

        if kpis["growth_pct"] >= 10:
            rules.append(
                (
                    "INFO",
                    "Strong revenue growth",
                    f"Revenue grew {kpis['growth_pct']:.1f}% vs the prior period (₹{kpis['revenue']:,.0f}).",
                    "growth_pct",
                    kpis["growth_pct"],
                    None,
                )
            )
        elif kpis["growth_pct"] <= -10:
            rules.append(
                (
                    "WARNING",
                    "Revenue decline detected",
                    f"Revenue dropped {abs(kpis['growth_pct']):.1f}% vs the prior period.",
                    "growth_pct",
                    kpis["growth_pct"],
                    None,
                )
            )

        if kpis["food_cost_pct"] > 35:
            rules.append(
                (
                    "ALERT",
                    "High food cost ratio",
                    f"Food cost is {kpis['food_cost_pct']:.1f}% of revenue — review recipes and waste.",
                    "food_cost_pct",
                    kpis["food_cost_pct"],
                    None,
                )
            )
        elif kpis["food_cost_pct"] < 25 and kpis["revenue"] > 0:
            rules.append(
                (
                    "INFO",
                    "Healthy food cost",
                    f"Food cost at {kpis['food_cost_pct']:.1f}% — within target range.",
                    "food_cost_pct",
                    kpis["food_cost_pct"],
                    None,
                )
            )

        if kpis["customer_retention"] >= 0.4:
            rules.append(
                (
                    "INFO",
                    "Solid customer retention",
                    f"{kpis['customer_retention']*100:.0f}% of period customers are returning guests.",
                    "customer_retention",
                    kpis["customer_retention"],
                    None,
                )
            )

        if inventory["low_stock"]:
            rules.append(
                (
                    "WARNING",
                    "Low stock items need attention",
                    f"{len(inventory['low_stock'])} products are at or below reorder level.",
                    "low_stock_count",
                    float(len(inventory["low_stock"])),
                    {"items": inventory["low_stock"][:5]},
                )
            )

        if inventory["dead_stock"]:
            rules.append(
                (
                    "INFO",
                    "Dead stock identified",
                    f"{len(inventory['dead_stock'])} products have zero sales in the lookback window.",
                    "dead_stock_count",
                    float(len(inventory["dead_stock"])),
                    None,
                )
            )

        low_margin = menu.get("lowest_margin", [])
        if low_margin and low_margin[0].get("margin_pct", 100) < 15:
            item = low_margin[0]
            rules.append(
                (
                    "WARNING",
                    "Low-margin menu item",
                    f"{item['name']} has {item['margin_pct']:.1f}% margin — consider repricing.",
                    "low_margin_item",
                    item["margin_pct"],
                    {"item": item},
                )
            )

        created: list[AnalyticsInsight] = []
        for severity, title, body, metric_key, metric_val, payload in rules:
            row = AnalyticsInsight(
                restaurant_id=restaurant_id,
                branch_id=branch_id,
                severity=severity,
                title=title,
                body=body,
                metric_key=metric_key,
                metric_value=Decimal(str(metric_val)) if metric_val is not None else None,
                payload=payload,
                created_by=actor_id,
                updated_by=actor_id,
            )
            self.db.add(row)
            created.append(row)

        self.db.commit()
        for row in created:
            self.db.refresh(row)
        return [_insight_out(r) for r in created]

    def list_insights(
        self,
        *,
        restaurant_id: UUID | None = None,
        branch_id: UUID | None = None,
        include_acknowledged: bool = False,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        stmt = select(AnalyticsInsight).where(AnalyticsInsight.is_deleted.is_(False))
        if restaurant_id is not None:
            stmt = stmt.where(AnalyticsInsight.restaurant_id == restaurant_id)
        if branch_id is not None:
            stmt = stmt.where(AnalyticsInsight.branch_id == branch_id)
        if not include_acknowledged:
            stmt = stmt.where(AnalyticsInsight.acknowledged.is_(False))
        stmt = stmt.order_by(AnalyticsInsight.created_at.desc()).limit(limit)
        return [_insight_out(r) for r in self.db.scalars(stmt).all()]

    def acknowledge_insight(self, insight_id: UUID, *, actor_id: int | None = None) -> dict[str, Any]:
        row = self.db.get(AnalyticsInsight, insight_id)
        if row is None or row.is_deleted:
            raise NotFoundError("AnalyticsInsight", str(insight_id))
        row.acknowledged = True
        row.acknowledged_at = datetime.now(timezone.utc)
        row.updated_by = actor_id
        self.db.commit()
        self.db.refresh(row)
        return _insight_out(row)

    def alert_center(
        self,
        *,
        restaurant_id: UUID | None = None,
        branch_id: UUID | None = None,
        actor_id: int | None = None,
        persist: bool = True,
    ) -> list[dict[str, Any]]:
        now = datetime.now(timezone.utc)
        week_start = now - timedelta(days=7)
        prior_start = week_start - timedelta(days=7)

        live: list[dict[str, Any]] = []

        inventory = self.smart_inventory(restaurant_id=restaurant_id, branch_id=branch_id)
        for item in inventory["low_stock"][:10]:
            live.append(
                {
                    "alert_type": "LOW_STOCK",
                    "severity": "WARNING",
                    "title": f"Low stock: {item['product_name']}",
                    "body": f"On hand {item['on_hand']} — reorder level {item['reorder_level']}.",
                    "payload": item,
                }
            )

        rev_now = self._sum_revenue(
            restaurant_id=restaurant_id, branch_id=branch_id, start=week_start, end=now
        )
        rev_prior = self._sum_revenue(
            restaurant_id=restaurant_id, branch_id=branch_id, start=prior_start, end=week_start
        )
        if rev_prior > 0:
            drop_pct = float((rev_prior - rev_now) / rev_prior * 100)
            if drop_pct > 15:
                live.append(
                    {
                        "alert_type": "REVENUE_DROP",
                        "severity": "ALERT",
                        "title": "Revenue drop vs prior week",
                        "body": f"Weekly revenue down {drop_pct:.1f}% compared to the previous week.",
                        "payload": {"drop_pct": drop_pct, "current": _flt(rev_now), "prior": _flt(rev_prior)},
                    }
                )

        kpis = self.executive_kpis(restaurant_id, branch_id, week_start, now)
        if kpis["food_cost_pct"] > 35:
            live.append(
                {
                    "alert_type": "HIGH_FOOD_COST",
                    "severity": "WARNING",
                    "title": "Elevated food cost",
                    "body": f"Food cost is {kpis['food_cost_pct']:.1f}% of revenue this week.",
                    "payload": {"food_cost_pct": kpis["food_cost_pct"]},
                }
            )

        cancel_stmt = (
            select(func.count())
            .select_from(Order)
            .where(
                Order.is_deleted.is_(False),
                Order.status == OrderStatus.CANCELLED,
                Order.order_date >= week_start,
                Order.order_date <= now,
            )
        )
        total_stmt = (
            select(func.count())
            .select_from(Order)
            .where(
                Order.is_deleted.is_(False),
                Order.order_date >= week_start,
                Order.order_date <= now,
            )
        )
        if branch_id is not None:
            cancel_stmt = cancel_stmt.where(Order.branch_id == branch_id)
            total_stmt = total_stmt.where(Order.branch_id == branch_id)
        elif restaurant_id is not None:
            cancel_stmt = cancel_stmt.join(Branch, Branch.id == Order.branch_id).where(
                Branch.restaurant_id == restaurant_id
            )
            total_stmt = total_stmt.join(Branch, Branch.id == Order.branch_id).where(
                Branch.restaurant_id == restaurant_id
            )
        cancelled = int(self.db.scalar(cancel_stmt) or 0)
        total_orders = int(self.db.scalar(total_stmt) or 0)
        cancel_rate = cancelled / total_orders * 100 if total_orders else 0
        if cancel_rate > 10 and cancelled >= 3:
            live.append(
                {
                    "alert_type": "HIGH_CANCELLATIONS",
                    "severity": "WARNING",
                    "title": "High cancellation rate",
                    "body": f"{cancel_rate:.1f}% of orders cancelled this week ({cancelled} orders).",
                    "payload": {"cancel_rate": cancel_rate, "cancelled": cancelled},
                }
            )

        if persist:
            notif = NotificationService(self.db)
            for alert in live:
                existing = self.db.scalars(
                    select(AnalyticsAlert).where(
                        AnalyticsAlert.restaurant_id == restaurant_id,
                        AnalyticsAlert.alert_type == alert["alert_type"],
                        AnalyticsAlert.is_resolved.is_(False),
                        AnalyticsAlert.is_deleted.is_(False),
                        AnalyticsAlert.title == alert["title"],
                    )
                ).first()
                if existing:
                    continue
                row = AnalyticsAlert(
                    restaurant_id=restaurant_id,
                    branch_id=branch_id,
                    alert_type=alert["alert_type"],
                    severity=alert["severity"],
                    title=alert["title"],
                    body=alert["body"],
                    payload=alert.get("payload"),
                    created_by=actor_id,
                    updated_by=actor_id,
                )
                self.db.add(row)
                if alert["severity"] in ("ALERT", "WARNING") and restaurant_id:
                    ntype = (
                        NotificationType.ALERT
                        if alert["severity"] == "ALERT"
                        else NotificationType.WARNING
                    )
                    notif.create(
                        title=alert["title"],
                        body=alert["body"],
                        notification_type=ntype,
                        restaurant_id=restaurant_id,
                    )
            self.db.commit()

        open_stmt = select(AnalyticsAlert).where(
            AnalyticsAlert.is_deleted.is_(False),
            AnalyticsAlert.is_resolved.is_(False),
        )
        if restaurant_id is not None:
            open_stmt = open_stmt.where(AnalyticsAlert.restaurant_id == restaurant_id)
        if branch_id is not None:
            open_stmt = open_stmt.where(AnalyticsAlert.branch_id == branch_id)
        open_stmt = open_stmt.order_by(AnalyticsAlert.created_at.desc()).limit(50)
        open_rows = self.db.scalars(open_stmt).all()

        stored = [_alert_out(r) for r in open_rows]
        return {"live": live, "open_alerts": stored}

    def resolve_alert(self, alert_id: UUID, *, actor_id: int | None = None) -> dict[str, Any]:
        row = self.db.get(AnalyticsAlert, alert_id)
        if row is None or row.is_deleted:
            raise NotFoundError("AnalyticsAlert", str(alert_id))
        row.is_resolved = True
        row.resolved_at = datetime.now(timezone.utc)
        row.updated_by = actor_id
        self.db.commit()
        self.db.refresh(row)
        return _alert_out(row)

    def _parse_question_range(self, q: str) -> tuple[datetime, datetime, str]:
        """Infer a date window from natural-language phrases in the question."""
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        if "today" in q:
            return today_start, now, "today"
        if "yesterday" in q:
            y0 = today_start - timedelta(days=1)
            return y0, today_start - timedelta(microseconds=1), "yesterday"
        if "this week" in q or "current week" in q:
            week_start = today_start - timedelta(days=today_start.weekday())
            return week_start, now, "this week"
        if "last week" in q or "past week" in q:
            week_start = today_start - timedelta(days=today_start.weekday())
            return week_start - timedelta(days=7), week_start - timedelta(microseconds=1), "last week"
        if "this month" in q or "current month" in q:
            month_start = today_start.replace(day=1)
            return month_start, now, "this month"
        if "last month" in q or "previous month" in q:
            month_start = today_start.replace(day=1)
            last_end = month_start - timedelta(microseconds=1)
            last_start = last_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            return last_start, last_end, "last month"
        if "this year" in q:
            year_start = today_start.replace(month=1, day=1)
            return year_start, now, "this year"

        start_dt, end_dt = self._resolve_range(None, None, default_days=30)
        return start_dt, end_dt, "last 30 days"

    @staticmethod
    def _inr(amount: float | int | Decimal | None) -> str:
        try:
            n = float(amount or 0)
        except (TypeError, ValueError):
            n = 0.0
        return f"₹{n:,.0f}"

    def _summarize_assistant_cards(
        self, cards: list[dict[str, Any]], *, period_label: str
    ) -> str:
        parts: list[str] = []
        for card in cards:
            d = card.get("data") or {}
            t = card.get("type")
            if t in ("sales", "overview"):
                growth = d.get("growth_pct")
                growth_bit = (
                    f" ({growth:+.1f}% vs prior period)" if growth is not None else ""
                )
                parts.append(
                    f"For {period_label}: revenue {self._inr(d.get('revenue'))}, "
                    f"profit {self._inr(d.get('profit'))}, "
                    f"{int(d.get('orders_count') or 0)} orders{growth_bit}."
                )
            elif t == "inventory":
                low = d.get("low_stock") or []
                parts.append(
                    f"Inventory value {self._inr(d.get('inventory_value'))} with "
                    f"{len(low)} item(s) at or below reorder."
                )
            elif t == "hr":
                parts.append(
                    f"Workforce: {int(d.get('employee_count') or 0)} staff, "
                    f"attendance {float(d.get('attendance_pct') or 0):.1f}%."
                )
            elif t == "customers":
                ret = d.get("retention_rate")
                ret_pct = f"{float(ret) * 100:.1f}%" if ret is not None else "—"
                parts.append(
                    f"Customers: {int(d.get('total_customers') or 0)} total, "
                    f"{int(d.get('vip_count') or 0)} VIP, retention {ret_pct}."
                )
            elif t == "menu":
                parts.append(
                    f"Tracking {int(d.get('total_items_tracked') or 0)} menu items "
                    f"for quantity, revenue, and margin."
                )
            elif t == "forecast":
                parts.append(
                    f"Forecast ({d.get('horizon') or 'week'}): "
                    f"predicted {self._inr(d.get('predicted_total_revenue'))}."
                )
        if not parts:
            return f"Pulled live BI for {period_label}."
        return " ".join(parts)

    def assistant_query(
        self,
        question: str,
        *,
        restaurant_id: UUID | None = None,
        branch_id: UUID | None = None,
    ) -> dict[str, Any]:
        q = question.lower().strip()
        start_dt, end_dt, period_label = self._parse_question_range(q)
        cards: list[dict[str, Any]] = []

        if any(w in q for w in ("sale", "revenue", "order", "profit", "kpi", "performance")):
            kpis = self.executive_kpis(restaurant_id, branch_id, start_dt, end_dt)
            cards.append(
                {
                    "type": "sales",
                    "title": "Sales Summary",
                    "period": period_label,
                    "data": kpis,
                }
            )

        if any(w in q for w in ("inventory", "stock", "reorder", "ingredient")):
            inv = self.smart_inventory(restaurant_id=restaurant_id, branch_id=branch_id)
            cards.append(
                {
                    "type": "inventory",
                    "title": "Inventory Status",
                    "period": period_label,
                    "data": inv,
                }
            )

        if any(w in q for w in ("staff", "employee", "attendance", "labor", "hr", "payroll")):
            emp = self.employee_analytics(
                restaurant_id=restaurant_id,
                branch_id=branch_id,
                start=start_dt,
                end=end_dt,
            )
            cards.append(
                {"type": "hr", "title": "Workforce", "period": period_label, "data": emp}
            )

        if any(w in q for w in ("customer", "loyalty", "retention", "vip")):
            cust = self.customer_analytics(
                restaurant_id=restaurant_id,
                branch_id=branch_id,
                start=start_dt,
                end=end_dt,
            )
            cards.append(
                {
                    "type": "customers",
                    "title": "Customer Analytics",
                    "period": period_label,
                    "data": cust,
                }
            )

        if any(w in q for w in ("menu", "dish", "margin")) or (
            "item" in q and "stock" not in q and "inventory" not in q
        ):
            menu = self.menu_analytics(
                restaurant_id=restaurant_id,
                branch_id=branch_id,
                start=start_dt,
                end=end_dt,
            )
            cards.append(
                {
                    "type": "menu",
                    "title": "Menu Performance",
                    "period": period_label,
                    "data": menu,
                }
            )

        if any(w in q for w in ("forecast", "predict", "demand", "tomorrow")):
            fc = self.sales_forecast(
                restaurant_id=restaurant_id,
                branch_id=branch_id,
                horizon="tomorrow" if "tomorrow" in q else "week",
            )
            cards.append(
                {
                    "type": "forecast",
                    "title": "Sales Forecast",
                    "period": period_label,
                    "data": fc,
                }
            )

        if not cards:
            kpis = self.executive_kpis(restaurant_id, branch_id, start_dt, end_dt)
            cards.append(
                {
                    "type": "overview",
                    "title": "Business Overview",
                    "period": period_label,
                    "data": kpis,
                }
            )

        return {
            "question": question,
            "period": period_label,
            "answer_summary": self._summarize_assistant_cards(cards, period_label=period_label),
            "cards": cards,
            "router": "keyword",
        }

    def export_report(
        self,
        kind: str,
        *,
        format: str = "csv",
        restaurant_id: UUID | None = None,
        branch_id: UUID | None = None,
    ) -> dict[str, Any]:
        kind = kind.lower()
        now = datetime.now(timezone.utc)
        if kind == "daily":
            start, end = now.replace(hour=0, minute=0, second=0, microsecond=0), now
            label = now.strftime("%Y%m%d")
        elif kind == "weekly":
            end = now
            start = now - timedelta(days=7)
            label = f"week_{now.strftime('%Y%m%d')}"
        elif kind == "monthly":
            end = now
            start = now - timedelta(days=30)
            label = now.strftime("%Y%m")
        else:
            raise ValidationError("kind must be daily, weekly, or monthly")

        kpis = self.executive_kpis(restaurant_id, branch_id, start, end)
        trend = self.revenue_trend(restaurant_id=restaurant_id, branch_id=branch_id, start=start, end=end)
        payments = self.payment_distribution(
            restaurant_id=restaurant_id, branch_id=branch_id, start=start, end=end
        )

        rows = [
            {"section": "kpis", "metric": k, "value": v}
            for k, v in kpis.items()
            if not isinstance(v, (dict, list))
        ]
        for t in trend:
            rows.append({"section": "daily_trend", "metric": t["date"], "value": t["revenue"]})
        for p in payments:
            rows.append(
                {"section": "payments", "metric": p["method"], "value": p["amount"]}
            )

        if format.lower() != "csv":
            raise ValidationError("Only csv format is supported")

        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=["section", "metric", "value"])
        writer.writeheader()
        writer.writerows(rows)
        filename = f"bi_report_{kind}_{label}.csv"

        return {
            "filename": filename,
            "content_type": "text/csv",
            "rows": rows,
            "csv": buf.getvalue(),
        }
