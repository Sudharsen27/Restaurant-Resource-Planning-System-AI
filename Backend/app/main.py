from contextlib import asynccontextmanager

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import api_router
from app.api.metrics import router as metrics_router
from app.core.config import settings
from app.core.constants import APP_VERSION
from app.core.exception_handlers import register_exception_handlers
from app.core.logging import setup_logging
from app.database.init_db import init_database, seed_placeholder_data
from app.middleware import (
    AuthenticationMiddleware,
    CsrfProtectionMiddleware,
    HttpsRedirectMiddleware,
    RateLimitMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    from app.ml.model_manager import ModelManager
    from app.ml.train import train_forecast_model

    setup_logging(level=settings.log_level, log_format=settings.log_format)

    if settings.sentry_dsn:
        try:
            import sentry_sdk
            from sentry_sdk.integrations.fastapi import FastApiIntegration
            from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

            sentry_sdk.init(
                dsn=settings.sentry_dsn,
                environment=settings.app_env,
                traces_sample_rate=settings.sentry_traces_sample_rate,
                integrations=[FastApiIntegration(), SqlalchemyIntegration()],
            )
        except Exception:
            pass

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
        description=(
            "Restaurant ERP SaaS Platform API — enterprise operations, "
            "inventory, POS, CRM/HRMS, analytics, multi-tenant SaaS, and platform ops."
        ),
        version=settings.app_version or APP_VERSION,
        debug=settings.debug,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        openapi_tags=[
            {"name": "health", "description": "Liveness, readiness, and detailed health"},
            {"name": "platform", "description": "Ops: cache, queue, backups, migrations, logs"},
            {"name": "metrics", "description": "Prometheus metrics"},
            {"name": "auth", "description": "Authentication & sessions"},
        ],
    )

    # Middleware order: last added runs first on request.
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(CsrfProtectionMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(AuthenticationMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(HttpsRedirectMiddleware)
    app.add_middleware(GZipMiddleware, minimum_size=500)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Response-Time-Ms", "X-RateLimit-Remaining"],
    )

    register_exception_handlers(app)
    app.include_router(api_router)
    app.include_router(metrics_router)

    uploads_dir = Path(__file__).resolve().parent.parent / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

    return app


app = create_app()
