from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.database.init_db import init_database, seed_placeholder_data
from app.utils.config import settings
from app.utils.exception_handlers import app_exception_handler
from app.utils.exceptions import AppException


@asynccontextmanager
async def lifespan(_app: FastAPI):
    import logging

    from app.ml.model_manager import ModelManager
    from app.ml.train import train_forecast_model

    logging.basicConfig(level=logging.INFO)

    init_database()
    seed_placeholder_data()

    from app.database.init_db import bootstrap_production_model_version

    manager = ModelManager()
    if not manager.models_exist():
        train_forecast_model()
    bootstrap_production_model_version()

    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        description="Self-Learning Forecaster API — Phase 6 Feedback Engine",
        version="0.6.0",
        debug=settings.debug,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(AppException, app_exception_handler)
    app.include_router(api_router)

    return app


app = create_app()
