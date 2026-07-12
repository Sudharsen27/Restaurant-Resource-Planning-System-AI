from fastapi import APIRouter

router = APIRouter(tags=["root"])


@router.get("/")
def root() -> dict:
    return {
        "message": "Restaurant Resource Planning System API",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "forecast": "/forecast",
            "forecast_predict": "/forecast/predict",
            "forecast_model_info": "/forecast/model-info",
            "forecast_retrain": "/forecast/retrain",
            "staff": "/staff",
            "inventory": "/inventory",
            "feedback": "/feedback",
            "dataset": "/dataset/info",
            "recommendation_staff": "/recommendation/staff",
            "recommendation_inventory": "/recommendation/inventory",
            "recommendation_full_plan": "/recommendation/full-plan",
            "feedback": "/feedback",
            "feedback_history": "/feedback/history",
            "model_versions": "/model/versions",
            "model_current": "/model/current",
            "model_retrain": "/model/retrain",
            "model_accuracy": "/model/accuracy",
        },
    }
