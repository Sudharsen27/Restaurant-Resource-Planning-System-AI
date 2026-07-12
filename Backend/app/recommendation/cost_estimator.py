"""Cost estimation for staff, inventory, and profit projections."""

import logging

from app.recommendation.rules import (
    AVERAGE_ORDER_VALUE,
    INGREDIENT_UNIT_PRICES,
    SHIFT_HOURS,
    STAFF_HOURLY_RATES,
)

logger = logging.getLogger(__name__)


def estimate_staff_cost(staff: dict[str, int]) -> float:
    total = sum(
        count * STAFF_HOURLY_RATES.get(role, 200) * SHIFT_HOURS
        for role, count in staff.items()
    )
    return round(total, 2)


def estimate_inventory_cost(ingredients: list[dict]) -> float:
    return round(sum(item.get("estimated_cost", 0) for item in ingredients), 2)


def estimate_revenue(predicted_customers: int, average_order_value: float | None = None) -> float:
    aov = average_order_value or AVERAGE_ORDER_VALUE
    return round(predicted_customers * aov, 2)


def estimate_profit(
    predicted_customers: int,
    staff_cost: float,
    inventory_cost: float,
    average_order_value: float | None = None,
) -> float:
    revenue = estimate_revenue(predicted_customers, average_order_value)
    profit = revenue - staff_cost - inventory_cost
    logger.info(
        "Cost estimate: revenue=%s staff=%s inventory=%s profit=%s",
        revenue,
        staff_cost,
        inventory_cost,
        profit,
    )
    return round(profit, 2)


def ingredient_line_cost(name: str, purchase_qty: float) -> float:
    unit_price = INGREDIENT_UNIT_PRICES.get(name, 50)
    return round(purchase_qty * unit_price, 2)
