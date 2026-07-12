import logging
from pathlib import Path
from typing import Any

import pandas as pd

from app.dataset.dataset_generator import generate_restaurant_dataset
from app.dataset.feature_engineering import apply_feature_engineering

logger = logging.getLogger(__name__)

DEFAULT_DATASET_PATH = Path(__file__).resolve().parents[2] / "dataset" / "restaurant_data.csv"


class DatasetLoader:
    """Load, validate, clean, and persist the restaurant historical dataset."""

    def __init__(self, file_path: Path | str | None = None) -> None:
        self.file_path = Path(file_path) if file_path else DEFAULT_DATASET_PATH

    def build_and_save(self, min_records: int = 10_000) -> pd.DataFrame:
        """Generate, engineer features, validate, and save the dataset."""
        raw_df = generate_restaurant_dataset(min_records=min_records)
        df = apply_feature_engineering(raw_df)
        df = self.remove_duplicates(df)
        df = self.check_missing_values(df)
        self.save(df)
        return df

    def load(self) -> pd.DataFrame:
        if not self.file_path.exists():
            logger.warning("Dataset not found at %s — generating now", self.file_path)
            return self.build_and_save()
        df = pd.read_csv(self.file_path, parse_dates=["date", "created_at"])
        if "local_event" in df.columns:
            df["local_event"] = df["local_event"].fillna("")
        return df

    def save(self, df: pd.DataFrame) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(self.file_path, index=False, na_rep="")
        logger.info("Dataset saved to %s (%s rows)", self.file_path, len(df))

    def remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        before = len(df)
        deduped = df.drop_duplicates(subset=["date", "hour"], keep="first")
        removed = before - len(deduped)
        if removed:
            logger.info("Removed %s duplicate rows", removed)
        return deduped

    def check_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        missing = df.isnull().sum()
        cols_with_missing = missing[missing > 0]
        if not cols_with_missing.empty:
            logger.warning("Missing values detected:\n%s", cols_with_missing)
        if "local_event" in df.columns:
            df["local_event"] = df["local_event"].fillna("")
        return df

    def validate(self, df: pd.DataFrame | None = None) -> dict[str, Any]:
        data = df if df is not None else self.load()
        missing = data.isnull().sum().to_dict()
        missing_filtered = {k: int(v) for k, v in missing.items() if v > 0}

        return {
            "valid": bool(len(data) >= 10_000 and data.duplicated(subset=["date", "hour"]).sum() == 0),
            "total_rows": int(len(data)),
            "duplicate_rows": int(data.duplicated(subset=["date", "hour"]).sum()),
            "missing_values": missing_filtered,
        }

    def get_info(self) -> dict[str, Any]:
        if not self.file_path.exists():
            return {
                "exists": False,
                "total_rows": 0,
                "columns": [],
                "missing_values": {},
                "min_date": None,
                "max_date": None,
                "dataset_size_mb": 0.0,
                "statistics": {},
            }

        df = pd.read_csv(self.file_path)
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
        if "local_event" in df.columns:
            df["local_event"] = df["local_event"].fillna("")
        missing = df.isnull().sum()
        missing_filtered = {k: int(v) for k, v in missing.items() if v > 0}
        size_mb = round(self.file_path.stat().st_size / (1024 * 1024), 3)

        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        statistics: dict[str, dict[str, float]] = {}
        for col in numeric_cols[:8]:
            statistics[col] = {
                "mean": round(float(df[col].mean()), 2),
                "min": round(float(df[col].min()), 2),
                "max": round(float(df[col].max()), 2),
            }

        min_date = None
        max_date = None
        if "date" in df.columns and df["date"].notna().any():
            min_date = str(df["date"].min().date())
            max_date = str(df["date"].max().date())

        return {
            "exists": True,
            "total_rows": len(df),
            "columns": df.columns.tolist(),
            "missing_values": missing_filtered,
            "min_date": min_date,
            "max_date": max_date,
            "dataset_size_mb": size_mb,
            "statistics": statistics,
        }

    def get_statistics_summary(self) -> dict[str, Any]:
        df = self.load()
        return {
            "total_rows": len(df),
            "columns": len(df.columns),
            "avg_actual_customers": round(float(df["actual_customers"].mean()), 2),
            "avg_total_sales": round(float(df["total_sales"].mean()), 2),
            "avg_food_wastage_kg": round(float(df["food_wastage_kg"].mean()), 2),
            "weekend_avg_customers": round(
                float(df.loc[df["is_weekend"], "actual_customers"].mean()), 2
            ),
            "weekday_avg_customers": round(
                float(df.loc[~df["is_weekend"], "actual_customers"].mean()), 2
            ),
            "promotion_avg_customers": round(
                float(df.loc[df["promotion"], "actual_customers"].mean()), 2
            ),
            "rainy_avg_customers": round(
                float(df.loc[df["rainfall"] > 5, "actual_customers"].mean()), 2
            ),
        }
