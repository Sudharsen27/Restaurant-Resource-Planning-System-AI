import logging

import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.feature_selection import SelectKBest, f_regression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.ml.preprocessing import (
    BOOLEAN_COLUMNS,
    CATEGORICAL_COLUMNS,
    FEATURE_COLUMNS,
    NUMERIC_COLUMNS,
)

logger = logging.getLogger(__name__)


def build_feature_pipeline(k_best: int = 18) -> ColumnTransformer:
  """Build preprocessing + feature selection pipeline."""
  numeric_features = [col for col in NUMERIC_COLUMNS if col in FEATURE_COLUMNS]
  boolean_features = [col for col in BOOLEAN_COLUMNS if col in FEATURE_COLUMNS]
  categorical_features = [col for col in CATEGORICAL_COLUMNS if col in FEATURE_COLUMNS]

  numeric_transformer = Pipeline(
      steps=[
          ("imputer", SimpleImputer(strategy="median")),
          ("scaler", StandardScaler()),
      ]
  )

  categorical_transformer = Pipeline(
      steps=[
          ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
      ]
  )

  preprocessor = ColumnTransformer(
      transformers=[
          ("num", numeric_transformer, numeric_features),
          ("bool", "passthrough", boolean_features),
          ("cat", categorical_transformer, categorical_features),
      ],
      remainder="drop",
  )

  pipeline = Pipeline(
      steps=[
          ("preprocessor", preprocessor),
          ("selector", SelectKBest(score_func=f_regression, k=k_best)),
      ]
  )

  logger.info("Feature pipeline built with %s input features", len(FEATURE_COLUMNS))
  return pipeline


def prepare_prediction_row(payload: dict) -> pd.DataFrame:
    """Convert API prediction payload into a single feature row."""
    from datetime import date as date_type

    record = dict(payload)
    forecast_date = record.get("date")
    if isinstance(forecast_date, str):
        forecast_date = date_type.fromisoformat(forecast_date)

    record["day_of_week"] = forecast_date.weekday()
    record["month"] = forecast_date.month
    record["is_weekend"] = record.get("is_weekend", forecast_date.weekday() >= 5)

    month = record["month"]
    if month in (12, 1, 2):
        record["season"] = "Winter"
    elif month in (3, 4, 5):
        record["season"] = "Spring"
    elif month in (6, 7, 8):
        record["season"] = "Summer"
    else:
        record["season"] = "Autumn"

    if not record.get("local_event"):
        record["local_event"] = "none"

    if record.get("average_order_value") is None:
        total_channel = (
            record.get("walk_in_customers", 0)
            + record.get("online_reservations", 0)
            + record.get("takeaway_orders", 0)
            + record.get("delivery_orders", 0)
        )
        record["average_order_value"] = 420.0 if total_channel > 0 else 380.0

    row = {col: record.get(col) for col in FEATURE_COLUMNS}
    frame = pd.DataFrame([row])

    for col in BOOLEAN_COLUMNS:
        if col in frame.columns:
            frame[col] = frame[col].astype(bool)

    for col in NUMERIC_COLUMNS:
        if col in frame.columns:
            frame[col] = pd.to_numeric(frame[col], errors="coerce").fillna(0)

    for col in CATEGORICAL_COLUMNS:
        if col in frame.columns:
            frame[col] = frame[col].fillna("none").astype(str)

    return frame


def tree_feature_importance(model, feature_pipeline: Pipeline, feature_names: list[str] | None = None) -> dict[str, float]:
    """Extract feature importance mapped to original feature names where possible."""
    if not hasattr(model, "feature_importances_"):
        return {}

    importances = model.feature_importances_
    if feature_names and len(feature_names) == len(importances):
        pairs = sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)
        return {name: round(float(score), 4) for name, score in pairs}

    return {f"feature_{i}": round(float(score), 4) for i, score in enumerate(importances)}
