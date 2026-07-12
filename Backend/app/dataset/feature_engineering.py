import logging
import math

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

ROLLING_WINDOW = 24


def apply_feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    """Add cyclical encodings, rolling metrics, and derived KPIs."""
    engineered = df.copy()

    engineered["hour_sin"] = np.sin(2 * math.pi * engineered["hour"] / 24)
    engineered["hour_cos"] = np.cos(2 * math.pi * engineered["hour"] / 24)
    engineered["day_sin"] = np.sin(2 * math.pi * engineered["day_of_week"] / 7)
    engineered["day_cos"] = np.cos(2 * math.pi * engineered["day_of_week"] / 7)

    engineered["rolling_average_customers"] = (
        engineered["actual_customers"]
        .rolling(window=ROLLING_WINDOW, min_periods=1)
        .mean()
        .round(2)
    )

    engineered["moving_average_sales"] = (
        engineered["total_sales"]
        .rolling(window=ROLLING_WINDOW, min_periods=1)
        .mean()
        .round(2)
    )

    engineered["customer_growth_rate"] = (
        engineered["actual_customers"].pct_change().fillna(0).replace([np.inf, -np.inf], 0).round(4)
    )

    total_ingredients = (
        engineered["ingredient_chicken_kg"]
        + engineered["ingredient_rice_kg"]
        + engineered["ingredient_onion_kg"]
        + engineered["ingredient_tomato_kg"]
        + engineered["ingredient_cheese_kg"]
    )
    engineered["inventory_utilization"] = (
        (total_ingredients / (engineered["actual_customers"] + 1) * 10)
        .clip(0, 2)
        .round(4)
    )

    total_staff = (
        engineered["chef_count"]
        + engineered["waiter_count"]
        + engineered["cashier_count"]
        + engineered["cleaner_count"]
    )
    engineered["staff_efficiency"] = (
        (engineered["actual_customers"] / total_staff.replace(0, 1))
        .round(4)
    )

    engineered["sales_per_customer"] = (
        (engineered["total_sales"] / engineered["actual_customers"].replace(0, 1))
        .round(2)
    )

    logger.info("Applied feature engineering (%s columns)", len(engineered.columns))
    return engineered
