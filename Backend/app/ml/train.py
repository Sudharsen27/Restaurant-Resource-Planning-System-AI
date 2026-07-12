import logging
from datetime import datetime, timezone
from typing import Any

from sklearn.ensemble import ExtraTreesRegressor, GradientBoostingRegressor, RandomForestRegressor
from sklearn.model_selection import train_test_split

from app.ml.evaluation import evaluate_model, plot_feature_importance, save_evaluation_report
from app.ml.feature_pipeline import build_feature_pipeline, tree_feature_importance
from app.ml.model_manager import ModelManager
from app.ml.preprocessing import FEATURE_COLUMNS, load_training_data, split_features_target

logger = logging.getLogger(__name__)


def _candidate_models() -> dict[str, Any]:
    return {
        "RandomForestRegressor": RandomForestRegressor(
            n_estimators=200,
            max_depth=18,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1,
        ),
        "GradientBoostingRegressor": GradientBoostingRegressor(
            n_estimators=200,
            learning_rate=0.08,
            max_depth=6,
            random_state=42,
        ),
        "ExtraTreesRegressor": ExtraTreesRegressor(
            n_estimators=200,
            max_depth=18,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1,
        ),
    }


def _rank_models(results: dict[str, dict[str, float]]) -> str:
    return sorted(
        results.items(),
        key=lambda item: (item[1]["rmse"], item[1]["mae"], -item[1]["r2"]),
    )[0][0]


def train_forecast_model(test_size: float = 0.2, random_state: int = 42) -> dict[str, Any]:
    """Train, compare, and persist the best customer forecast model."""
    logger.info("Starting model training pipeline")

    df = load_training_data()
    x_data, y_data = split_features_target(df)

    x_train, x_test, y_train, y_test = train_test_split(
        x_data,
        y_data,
        test_size=test_size,
        random_state=random_state,
    )

    feature_pipeline = build_feature_pipeline()
    x_train_transformed = feature_pipeline.fit_transform(x_train, y_train)
    x_test_transformed = feature_pipeline.transform(x_test)

    comparison: dict[str, dict[str, float]] = {}
    trained_models: dict[str, Any] = {}

    for name, model in _candidate_models().items():
        logger.info("Training %s", name)
        model.fit(x_train_transformed, y_train)
        predictions = model.predict(x_test_transformed)
        comparison[name] = evaluate_model(y_test, predictions)
        trained_models[name] = model

    best_name = _rank_models(comparison)
    best_model = trained_models[best_name]
    best_metrics = comparison[best_name]

    logger.info("Best model selected: %s (RMSE=%s, MAE=%s, R²=%s)", best_name, best_metrics["rmse"], best_metrics["mae"], best_metrics["r2"])

    importance = tree_feature_importance(best_model, feature_pipeline, FEATURE_COLUMNS)
    chart_path = plot_feature_importance(importance)

    report = {
        "model_name": best_name,
        "metrics": best_metrics,
        "model_comparison": comparison,
        "feature_importance": importance,
        "feature_importance_chart": str(chart_path),
        "dataset_size": len(df),
        "training_samples": len(x_train),
        "test_samples": len(x_test),
    }
    save_evaluation_report(report)

    metadata = {
        "model_name": best_name,
        "training_date": datetime.now(timezone.utc).isoformat(),
        "features_used": FEATURE_COLUMNS,
        "dataset_size": len(df),
        "metrics": best_metrics,
        "model_comparison": comparison,
        "feature_importance": importance,
    }

    manager = ModelManager()
    manager.save(best_model, feature_pipeline, metadata)

    print("\n=== Model Training Complete ===")
    print(f"Best Model: {best_name}")
    print(f"MAE:  {best_metrics['mae']}")
    print(f"RMSE: {best_metrics['rmse']}")
    print(f"R²:   {best_metrics['r2']}")
    print(f"Accuracy: {best_metrics['accuracy']}%")
    print("\nModel Comparison:")
    for model_name, metrics in comparison.items():
        print(f"  {model_name}: MAE={metrics['mae']}, RMSE={metrics['rmse']}, R²={metrics['r2']}")

    return report
