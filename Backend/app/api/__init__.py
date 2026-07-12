from fastapi import APIRouter

from app.api.dataset import router as dataset_router
from app.api.feedback_learning import router as feedback_learning_router
from app.api.forecast import router as forecast_router
from app.api.forecast_ml import router as forecast_ml_router
from app.api.health import router as health_router
from app.api.inventory import router as inventory_router
from app.api.latest_snapshots import router as latest_snapshots_router
from app.api.model_learning import router as model_learning_router
from app.api.recommendation import router as recommendation_router
from app.api.root import router as root_router
from app.api.staff import router as staff_router

api_router = APIRouter()
api_router.include_router(root_router)
api_router.include_router(health_router)
api_router.include_router(latest_snapshots_router)
api_router.include_router(forecast_ml_router)
api_router.include_router(forecast_router)
api_router.include_router(staff_router)
api_router.include_router(inventory_router)
api_router.include_router(feedback_learning_router)
api_router.include_router(dataset_router)
api_router.include_router(recommendation_router)
api_router.include_router(model_learning_router)
