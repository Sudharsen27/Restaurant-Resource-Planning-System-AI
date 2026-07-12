import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

DEFAULT_DATASET_PATH = Path(__file__).resolve().parents[2] / "dataset" / "restaurant_data.csv"

TARGET_COLUMN = "actual_customers"

FEATURE_COLUMNS = [
    "hour",
    "day_of_week",
    "month",
    "is_weekend",
    "is_holiday",
    "season",
    "temperature",
    "rainfall",
    "promotion",
    "local_event",
    "previous_hour_customers",
    "previous_day_customers",
    "walk_in_customers",
    "online_reservations",
    "takeaway_orders",
    "delivery_orders",
    "average_order_value",
    "kitchen_load",
    "table_utilization",
    "supplier_delay_days",
]

CATEGORICAL_COLUMNS = ["season", "local_event"]
NUMERIC_COLUMNS = [
    "hour",
    "day_of_week",
    "month",
    "temperature",
    "rainfall",
    "previous_hour_customers",
    "previous_day_customers",
    "walk_in_customers",
    "online_reservations",
    "takeaway_orders",
    "delivery_orders",
    "average_order_value",
    "kitchen_load",
    "table_utilization",
    "supplier_delay_days",
]
BOOLEAN_COLUMNS = ["is_weekend", "is_holiday", "promotion"]


def load_training_data(file_path: Path | str | None = None) -> pd.DataFrame:
    path = Path(file_path) if file_path else DEFAULT_DATASET_PATH
    if not path.exists():
        raise FileNotFoundError(f"Training dataset not found: {path}")

    df = pd.read_csv(path, parse_dates=["date"])
    logger.info("Loaded training dataset: %s rows from %s", len(df), path)
    return df


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Handle missing values and normalize types."""
    cleaned = df.copy()

    if "local_event" in cleaned.columns:
        cleaned["local_event"] = cleaned["local_event"].fillna("").astype(str)
        cleaned.loc[cleaned["local_event"].str.strip() == "", "local_event"] = "none"

    for col in BOOLEAN_COLUMNS:
        if col in cleaned.columns:
            cleaned[col] = cleaned[col].fillna(False).astype(bool)

    for col in NUMERIC_COLUMNS:
        if col in cleaned.columns:
            cleaned[col] = pd.to_numeric(cleaned[col], errors="coerce")
            cleaned[col] = cleaned[col].fillna(cleaned[col].median())

    if "season" in cleaned.columns:
        cleaned["season"] = cleaned["season"].fillna("Unknown").astype(str)

    cleaned = cleaned.dropna(subset=[TARGET_COLUMN])
    return cleaned


def split_features_target(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    cleaned = clean_dataframe(df)
    missing_features = [col for col in FEATURE_COLUMNS if col not in cleaned.columns]
    if missing_features:
        raise ValueError(f"Missing feature columns in dataset: {missing_features}")

    x_data = cleaned[FEATURE_COLUMNS]
    y_data = cleaned[TARGET_COLUMN]
    return x_data, y_data
