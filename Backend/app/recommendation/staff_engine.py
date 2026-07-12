"""Staff scheduling recommendation engine."""

import logging
import math

from app.recommendation.rules import STAFF_RULES

logger = logging.getLogger(__name__)


def _ceil_ratio(customers: int, per_customers: int, minimum: int = 0) -> int:
    if per_customers <= 0:
        return minimum
    return max(minimum, math.ceil(customers / per_customers))


def recommend_staff(predicted_customers: int) -> dict[str, int]:
    """Generate staff counts from predicted customer demand."""
    if predicted_customers < 1:
        raise ValueError("predicted_customers must be at least 1")

    rules = STAFF_RULES

    cashier_count = rules["cashier"]["minimum"]
    if predicted_customers > rules["cashier"]["additional_every"]:
        extra_cashiers = math.ceil(
            (predicted_customers - rules["cashier"]["additional_every"])
            / rules["cashier"]["additional_every"]
        )
        cashier_count += extra_cashiers

    staff = {
        "chef": _ceil_ratio(
            predicted_customers,
            rules["chef"]["per_customers"],
            rules["chef"]["minimum"],
        ),
        "waiter": _ceil_ratio(
            predicted_customers,
            rules["waiter"]["per_customers"],
            rules["waiter"]["minimum"],
        ),
        "kitchen_helper": _ceil_ratio(
            predicted_customers,
            rules["kitchen_helper"]["per_customers"],
            rules["kitchen_helper"]["minimum"],
        ),
        "cashier": cashier_count,
        "cleaner": _ceil_ratio(
            predicted_customers,
            rules["cleaner"]["per_customers"],
            rules["cleaner"]["minimum"],
        ),
        "host": max(
            rules["host"].get("minimum", 0),
            predicted_customers // rules["host"]["per_customers"],
        ) if predicted_customers >= rules["host"]["per_customers"] else rules["host"].get("minimum", 0),
        "manager": rules["manager"]["minimum"],
    }

    logger.info(
        "Staff recommendation for %s customers: %s total staff",
        predicted_customers,
        sum(staff.values()),
    )
    return staff
