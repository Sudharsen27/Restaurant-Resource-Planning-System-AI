from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.config import settings
from app.core.constants import APP_VERSION
from app.core.exception_handlers import register_exception_handlers
from app.core.logging import setup_logging
from app.database.init_db import init_database, seed_placeholder_data
from app.middleware import (
    RateLimitMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    from app.ml.model_manager import ModelManager
    from app.ml.train import train_forecast_model

    setup_logging(level=settings.log_level, log_format=settings.log_format)

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
        version=APP_VERSION,
        debug=settings.debug,
        lifespan=lifespan,
    )

    # Middleware order: last added runs first on request.
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(api_router)

    return app


app = create_app()
