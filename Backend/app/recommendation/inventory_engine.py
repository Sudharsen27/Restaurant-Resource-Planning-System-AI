"""Ingredient procurement recommendation engine."""

import logging
import math
from collections import defaultdict

from app.recommendation.cost_estimator import ingredient_line_cost
from app.recommendation.rules import (
    DEFAULT_SAFETY_STOCK_RATE,
    DEFAULT_WASTAGE_RATE,
    INGREDIENT_SHELF_LIFE_DAYS,
    INGREDIENT_UNITS,
    MENU_MIX,
    MENU_RECIPES,
)

logger = logging.getLogger(__name__)


def _estimate_menu_orders(predicted_customers: int) -> dict[str, int]:
    orders: dict[str, int] = {}
    for menu_item, share in MENU_MIX.items():
        orders[menu_item] = max(1, round(predicted_customers * share))
    return orders


def _calculate_raw_consumption(menu_orders: dict[str, int]) -> dict[str, float]:
    consumption: dict[str, float] = defaultdict(float)
    for menu_item, order_count in menu_orders.items():
        recipe = MENU_RECIPES.get(menu_item, {})
        for ingredient, qty_per_serving in recipe.items():
            consumption[ingredient] += order_count * qty_per_serving
    return dict(consumption)


def _lead_time_buffer(required: float, supplier_lead_time_days: float, shelf_life_days: int) -> float:
    """Increase order when lead time is long relative to shelf life."""
    if shelf_life_days <= 0:
        return required
    lead_factor = min(0.25, supplier_lead_time_days / max(shelf_life_days, 1) * 0.1)
    return required * (1 + lead_factor)


def recommend_inventory(
    predicted_customers: int,
    current_inventory: dict[str, float] | None = None,
    safety_stock_rate: float = DEFAULT_SAFETY_STOCK_RATE,
    wastage_rate: float = DEFAULT_WASTAGE_RATE,
    supplier_lead_time_days: float = 1.0,
) -> list[dict]:
    """
    Convert predicted demand into ingredient purchase recommendations.

    Flow: menu sales → consumption → safety stock → subtract current → purchase qty → cost
    """
    if predicted_customers < 1:
        raise ValueError("predicted_customers must be at least 1")

    current = current_inventory or {}
    menu_orders = _estimate_menu_orders(predicted_customers)
    raw_consumption = _calculate_raw_consumption(menu_orders)

    ingredients: list[dict] = []

    for name, required_qty in sorted(raw_consumption.items()):
        wastage = required_qty * wastage_rate
        with_wastage = required_qty + wastage
        safety_stock = with_wastage * safety_stock_rate
        gross_required = with_wastage + safety_stock

        shelf_life = INGREDIENT_SHELF_LIFE_DAYS.get(name, 14)
        gross_required = _lead_time_buffer(gross_required, supplier_lead_time_days, shelf_life)

        on_hand = current.get(name, 0.0)
        purchase_qty = max(0.0, gross_required - on_hand)

        if purchase_qty > 0 and INGREDIENT_UNITS.get(name) == "pcs":
            purchase_qty = float(math.ceil(purchase_qty))

        purchase_qty = round(purchase_qty, 2)
        required_rounded = round(gross_required, 2)

        ingredients.append(
            {
                "name": name,
                "required": required_rounded,
                "unit": INGREDIENT_UNITS.get(name, "kg"),
                "purchase": purchase_qty,
                "estimated_cost": ingredient_line_cost(name, purchase_qty),
                "shelf_life_days": shelf_life,
            }
        )

    logger.info(
        "Inventory recommendation for %s customers: %s ingredients, purchase items=%s",
        predicted_customers,
        len(ingredients),
        sum(1 for i in ingredients if i["purchase"] > 0),
    )
    return ingredients
