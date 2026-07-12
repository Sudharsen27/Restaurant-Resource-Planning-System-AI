import logging
import math
import random
from datetime import date, datetime
from typing import Any

import numpy as np
import pandas as pd
from faker import Faker

logger = logging.getLogger(__name__)

fake = Faker()
Faker.seed(42)
np.random.seed(42)
random.seed(42)

# Minimum records and ~1 year of hourly operations (417 days × 24h > 10,000)
MIN_RECORDS = 10_000
HOURS_PER_DAY = 24
GENERATION_DAYS = math.ceil(MIN_RECORDS / HOURS_PER_DAY)

START_DATE = date(2024, 1, 1)

HOLIDAYS: set[date] = {
    date(2024, 1, 1),
    date(2024, 1, 26),
    date(2024, 3, 25),
    date(2024, 8, 15),
    date(2024, 10, 2),
    date(2024, 10, 31),
    date(2024, 11, 1),
    date(2024, 12, 25),
    date(2024, 12, 31),
    date(2025, 1, 1),
    date(2025, 1, 26),
    date(2025, 3, 14),
    date(2025, 8, 15),
    date(2025, 10, 2),
    date(2025, 12, 25),
}

LOCAL_EVENTS = [
    "Food Festival Downtown",
    "City Marathon",
    "University Graduation Week",
    "Concert at Central Park",
    "Cricket Match Nearby",
    "Street Fair",
    "Corporate Conference",
    "Holiday Market",
    "Farmers Market",
    "Tech Summit",
]

WEATHER_CONDITIONS = ["Sunny", "Cloudy", "Rainy", "Stormy", "Windy", "Humid"]


def _season(month: int) -> str:
    if month in (12, 1, 2):
        return "Winter"
    if month in (3, 4, 5):
        return "Spring"
    if month in (6, 7, 8):
        return "Summer"
    return "Autumn"


def _hourly_demand_profile(hour: int) -> float:
    """Lunch and dinner peaks; late night trough."""
    if 11 <= hour <= 14:
        return 1.0 + 0.35 * math.sin((hour - 11) * math.pi / 3)
    if 18 <= hour <= 21:
        return 1.0 + 0.45 * math.sin((hour - 18) * math.pi / 3)
    if 7 <= hour <= 10:
        return 0.55 + 0.1 * (hour - 7)
    if 15 <= hour <= 17:
        return 0.5
    if 22 <= hour or hour <= 2:
        return 0.12 + 0.03 * max(0, 2 - hour if hour <= 2 else 0)
    return 0.25


def _base_temperature(month: int, hour: int) -> float:
    seasonal = {1: 18, 2: 20, 3: 24, 4: 28, 5: 32, 6: 35, 7: 33, 8: 32, 9: 30, 10: 27, 11: 22, 12: 18}
    daily_variation = 4 * math.sin((hour - 6) * math.pi / 12)
    return seasonal.get(month, 25) + daily_variation + np.random.normal(0, 1.5)


def _weather_label(temperature: float, rainfall: float) -> str:
    if rainfall > 8:
        return "Stormy" if rainfall > 20 else "Rainy"
    if temperature > 34:
        return "Humid"
    if temperature < 12:
        return "Windy"
    if rainfall > 2:
        return "Cloudy"
    return random.choice(["Sunny", "Cloudy"])


def generate_restaurant_dataset(
    min_records: int = MIN_RECORDS,
    start_date: date = START_DATE,
) -> pd.DataFrame:
    """
    Generate a realistic hourly restaurant operations dataset.

    Simulates extended hourly operations (~417 days) to exceed 10,000 records
    while preserving realistic daily and seasonal patterns.
    """
    total_hours = max(min_records, GENERATION_DAYS * HOURS_PER_DAY)
    logger.info("Generating %s hourly restaurant records from %s", total_hours, start_date)

    timestamps = pd.date_range(
        datetime.combine(start_date, datetime.min.time()),
        periods=total_hours,
        freq="h",
    )

    records: list[dict[str, Any]] = []
    prev_day_customers = 80
    prev_hour_customers = 20

    for ts in timestamps:
        current_date = ts.date()
        hour = ts.hour
        day_of_week = ts.dayofweek
        month = ts.month
        is_weekend = day_of_week >= 5
        is_holiday = current_date in HOLIDAYS
        season = _season(month)

        temperature = round(_base_temperature(month, hour), 1)
        rainfall = round(max(0, np.random.exponential(2.5) if month in (6, 7, 8, 9) else np.random.exponential(1.2)), 2)
        weather = _weather_label(temperature, rainfall)

        promotion = random.random() < 0.12
        local_event = random.random() < 0.06
        event_name = random.choice(LOCAL_EVENTS) if local_event else ""

        demand = _hourly_demand_profile(hour) * 95

        if is_weekend:
            demand *= 1.35
        if is_holiday:
            demand *= 1.45
        if promotion:
            demand *= 1.28
        if local_event:
            demand *= 1.22
        if rainfall > 5:
            demand *= 0.78
        elif rainfall > 2:
            demand *= 0.9
        if season == "Summer" and 12 <= hour <= 16:
            demand *= 1.08
        if season == "Winter" and hour >= 18:
            demand *= 1.05
        if temperature > 36:
            demand *= 0.92
        if temperature < 8:
            demand *= 0.88

        noise = np.random.normal(0, 8)
        actual_customers = max(5, int(round(demand + noise)))

        prediction_bias = np.random.normal(0, 6)
        if promotion:
            prediction_bias += 4
        if rainfall > 5:
            prediction_bias += 5
        predicted_customers = max(5, int(round(actual_customers + prediction_bias)))

        walk_in_share = 0.42
        if rainfall > 5:
            walk_in_share = 0.22
        elif is_weekend:
            walk_in_share = 0.48

        walk_in = int(actual_customers * walk_in_share * np.random.uniform(0.9, 1.1))
        remaining = max(0, actual_customers - walk_in)
        online = int(remaining * np.random.uniform(0.25, 0.35))
        takeaway = int(remaining * np.random.uniform(0.30, 0.40))
        delivery = max(0, actual_customers - walk_in - online - takeaway)

        avg_order = round(np.random.uniform(280, 520) * (1.05 if promotion else 1.0), 2)
        total_sales = round(actual_customers * avg_order * np.random.uniform(0.92, 1.08), 2)

        table_utilization = round(min(0.98, actual_customers / max(1, 120) * np.random.uniform(0.85, 1.1)), 3)
        kitchen_load = round(min(1.0, actual_customers / 100 * np.random.uniform(0.9, 1.15)), 3)

        chef_count = max(1, int(np.ceil(actual_customers / 35)))
        waiter_count = max(2, int(np.ceil(actual_customers / 18)))
        cashier_count = max(1, int(np.ceil(actual_customers / 60)))
        cleaner_count = max(1, int(np.ceil(actual_customers / 80)))

        chicken = round(actual_customers * np.random.uniform(0.08, 0.14), 2)
        rice = round(actual_customers * np.random.uniform(0.06, 0.11), 2)
        oil = round(actual_customers * np.random.uniform(0.008, 0.015), 2)
        onion = round(actual_customers * np.random.uniform(0.03, 0.06), 2)
        tomato = round(actual_customers * np.random.uniform(0.025, 0.05), 2)
        cheese = round(actual_customers * np.random.uniform(0.02, 0.04), 2)
        milk = round(actual_customers * np.random.uniform(0.015, 0.03), 2)

        inventory_cost = round(
            chicken * 15 + rice * 3 + oil * 12 + onion * 2 + tomato * 2.5 + cheese * 8 + milk * 4,
            2,
        )
        supplier_delay = round(max(0, np.random.exponential(1.2) + (2 if rainfall > 8 else 0)), 1)

        over_prediction = max(0, predicted_customers - actual_customers)
        food_wastage = round(over_prediction * np.random.uniform(0.04, 0.09) + np.random.uniform(0.5, 2.5), 2)

        satisfaction = round(
            min(5.0, max(2.5, 4.2 - 0.02 * over_prediction - 0.03 * kitchen_load * 10 + np.random.normal(0, 0.15))),
            2,
        )

        records.append(
            {
                "date": current_date.isoformat(),
                "hour": hour,
                "day_of_week": day_of_week,
                "month": month,
                "is_weekend": is_weekend,
                "is_holiday": is_holiday,
                "season": season,
                "temperature": temperature,
                "rainfall": rainfall,
                "weather": weather,
                "promotion": promotion,
                "local_event": event_name if local_event else "",
                "previous_hour_customers": prev_hour_customers,
                "previous_day_customers": prev_day_customers,
                "predicted_customers": predicted_customers,
                "actual_customers": actual_customers,
                "walk_in_customers": walk_in,
                "online_reservations": online,
                "takeaway_orders": takeaway,
                "delivery_orders": delivery,
                "average_order_value": avg_order,
                "total_sales": total_sales,
                "kitchen_load": kitchen_load,
                "table_utilization": table_utilization,
                "chef_count": chef_count,
                "waiter_count": waiter_count,
                "cashier_count": cashier_count,
                "cleaner_count": cleaner_count,
                "ingredient_chicken_kg": chicken,
                "ingredient_rice_kg": rice,
                "ingredient_oil_l": oil,
                "ingredient_onion_kg": onion,
                "ingredient_tomato_kg": tomato,
                "ingredient_cheese_kg": cheese,
                "ingredient_milk_l": milk,
                "inventory_cost": inventory_cost,
                "supplier_delay_days": supplier_delay,
                "food_wastage_kg": food_wastage,
                "customer_satisfaction": satisfaction,
                "created_at": ts.isoformat(),
            }
        )

        prev_hour_customers = actual_customers
        if hour == 23:
            prev_day_customers = sum(
                r["actual_customers"] for r in records[-24:]
            ) if len(records) >= 24 else actual_customers * 12

    df = pd.DataFrame(records)
    logger.info("Generated %s raw records", len(df))
    return df
