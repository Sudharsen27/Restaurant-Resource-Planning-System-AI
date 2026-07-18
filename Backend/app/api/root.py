from fastapi import APIRouter

from app.core.constants import API_V1_PREFIX, APP_VERSION

router = APIRouter(tags=["root"])


@router.get("/")
def root() -> dict:
    prefix = API_V1_PREFIX
    return {
        "message": "Restaurant Resource Planning System API",
        "version": APP_VERSION,
        "docs": "/docs",
        "api_prefix": prefix,
        "health": f"{prefix}/health",
        "endpoints": {
            "forecast": f"{prefix}/forecast",
            "forecast_predict": f"{prefix}/forecast/predict",
            "forecast_model_info": f"{prefix}/forecast/model-info",
            "forecast_retrain": f"{prefix}/forecast/retrain",
            "forecast_latest": f"{prefix}/forecast/latest",
            "staff": f"{prefix}/staff",
            "staff_latest": f"{prefix}/staff/latest",
            "inventory": f"{prefix}/inventory",
            "inventory_latest": f"{prefix}/inventory/latest",
            "dashboard_latest": f"{prefix}/dashboard/latest",
            "feedback": f"{prefix}/feedback",
            "feedback_history": f"{prefix}/feedback/history",
            "dataset": f"{prefix}/dataset/info",
            "recommendation_staff": f"{prefix}/recommendation/staff",
            "recommendation_inventory": f"{prefix}/recommendation/inventory",
            "recommendation_full_plan": f"{prefix}/recommendation/full-plan",
            "model_versions": f"{prefix}/model/versions",
            "model_current": f"{prefix}/model/current",
            "model_retrain": f"{prefix}/model/retrain",
            "model_accuracy": f"{prefix}/model/accuracy",
        },
        "legacy_note": "Unversioned root paths remain available for backward compatibility.",
    }
