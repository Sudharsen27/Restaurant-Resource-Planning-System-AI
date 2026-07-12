import logging
from datetime import date, timedelta

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.feedback.model_versioning import METADATA_DIR
from app.models.accuracy_history import AccuracyHistory
from app.models.model_version import ModelVersion
from app.models.prediction_history import PredictionHistory

logger = logging.getLogger(__name__)

ACCURACY_CSV_PATH = METADATA_DIR / "accuracy_history.csv"


class AccuracyTracker:
    """Track and report prediction accuracy over time."""

    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def calculate_errors(predicted: float, actual: float) -> dict[str, float]:
        absolute_error = abs(actual - predicted)
        percentage_error = (absolute_error / max(actual, 1)) * 100
        mape = (absolute_error / max(actual, 1)) * 100
        return {
            "absolute_error": round(absolute_error, 4),
            "percentage_error": round(percentage_error, 4),
            "mape": round(mape, 4),
        }

    def record_accuracy_snapshot(self, model_version_id: int | None, metrics: dict[str, float]) -> AccuracyHistory:
        entry = AccuracyHistory(
            recorded_date=date.today(),
            accuracy=metrics.get("accuracy", 0.0),
            mae=metrics.get("mae", 0.0),
            rmse=metrics.get("rmse", 0.0),
            mape=metrics.get("mape", metrics.get("average_error", 0.0)),
            average_error=metrics.get("mae", 0.0),
            model_version_id=model_version_id,
        )
        self.db.add(entry)
        self.db.flush()
        self.export_accuracy_csv()
        logger.info("Recorded accuracy snapshot for model version id=%s", model_version_id)
        return entry

    def export_accuracy_csv(self) -> None:
        rows = self.db.scalars(select(AccuracyHistory).order_by(AccuracyHistory.recorded_date)).all()
        data = [
            {
                "recorded_date": row.recorded_date.isoformat(),
                "accuracy": row.accuracy,
                "mae": row.mae,
                "rmse": row.rmse,
                "mape": row.mape,
                "average_error": row.average_error,
                "model_version_id": row.model_version_id,
            }
            for row in rows
        ]
        METADATA_DIR.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(data).to_csv(ACCURACY_CSV_PATH, index=False)
        logger.info("Exported accuracy history CSV (%s rows)", len(data))

    def get_feedback_accuracy_stats(self) -> dict[str, float | None]:
        stmt = select(
            func.avg(PredictionHistory.percentage_error),
            func.avg(PredictionHistory.absolute_error),
            func.avg(PredictionHistory.mape),
            func.count(PredictionHistory.id),
        ).where(PredictionHistory.actual_customers.is_not(None))

        avg_pct, avg_abs, avg_mape, count = self.db.execute(stmt).one()
        if not count:
            return {
                "average_percentage_error": None,
                "average_absolute_error": None,
                "average_mape": None,
                "feedback_count": 0,
            }

        accuracy = max(0.0, 100.0 - float(avg_pct or 0.0))
        return {
            "average_percentage_error": round(float(avg_pct or 0.0), 4),
            "average_absolute_error": round(float(avg_abs or 0.0), 4),
            "average_mape": round(float(avg_mape or 0.0), 4),
            "feedback_count": int(count),
            "overall_accuracy": round(accuracy, 2),
        }

    def get_dashboard(self) -> dict:
        today = date.today()
        thirty_days_ago = today - timedelta(days=30)

        today_stmt = select(PredictionHistory).where(
            PredictionHistory.forecast_date == today,
            PredictionHistory.actual_customers.is_not(None),
        )
        today_rows = list(self.db.scalars(today_stmt).all())

        last_30_stmt = select(PredictionHistory).where(
            PredictionHistory.forecast_date >= thirty_days_ago,
            PredictionHistory.actual_customers.is_not(None),
        )
        last_30_rows = list(self.db.scalars(last_30_stmt).all())

        def _accuracy(rows: list[PredictionHistory]) -> float | None:
            if not rows:
                return None
            errors = [row.percentage_error or 0.0 for row in rows]
            return round(max(0.0, 100.0 - (sum(errors) / len(errors))), 2)

        feedback_stats = self.get_feedback_accuracy_stats()
        versions = list(self.db.scalars(select(ModelVersion).order_by(ModelVersion.accuracy.desc())).all())
        current = self.db.scalar(select(ModelVersion).where(ModelVersion.is_production.is_(True)).limit(1))
        latest = self.db.scalar(select(ModelVersion).order_by(ModelVersion.id.desc()).limit(1))

        return {
            "todays_accuracy": _accuracy(today_rows),
            "last_30_days_accuracy": _accuracy(last_30_rows),
            "overall_accuracy": feedback_stats.get("overall_accuracy"),
            "average_error": feedback_stats.get("average_absolute_error"),
            "average_mape": feedback_stats.get("average_mape"),
            "feedback_count": feedback_stats.get("feedback_count", 0),
            "best_model": versions[0].version_label if versions else None,
            "latest_model": latest.version_label if latest else None,
            "current_production_model": current.version_label if current else None,
        }
