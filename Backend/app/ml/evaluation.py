import json
import logging
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).resolve().parents[2] / "models"


def evaluate_model(y_true, y_pred) -> dict[str, float]:
    mae = mean_absolute_error(y_true, y_pred)
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    r2 = r2_score(y_true, y_pred)

    metrics = {
        "mae": round(float(mae), 4),
        "rmse": round(rmse, 4),
        "r2": round(float(r2), 4),
        "accuracy": round(float(r2) * 100, 2),
    }
    logger.info("Evaluation metrics: %s", metrics)
    return metrics


def save_evaluation_report(report: dict[str, Any], path: Path | None = None) -> Path:
    output = path or MODELS_DIR / "evaluation_report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)
    logger.info("Evaluation report saved to %s", output)
    return output


def plot_feature_importance(
    importance: dict[str, float],
    path: Path | None = None,
    top_n: int = 15,
) -> Path:
    output = path or MODELS_DIR / "feature_importance.png"
    output.parent.mkdir(parents=True, exist_ok=True)

    sorted_items = sorted(importance.items(), key=lambda item: item[1], reverse=True)[:top_n]
    if not sorted_items:
        sorted_items = [("no_features", 0.0)]

    labels, values = zip(*sorted_items)

    plt.figure(figsize=(10, 6))
    plt.barh(labels[::-1], values[::-1], color="#2563eb")
    plt.xlabel("Importance")
    plt.title("Customer Forecast Model — Feature Importance")
    plt.tight_layout()
    plt.savefig(output, dpi=120)
    plt.close()

    logger.info("Feature importance chart saved to %s", output)
    return output
