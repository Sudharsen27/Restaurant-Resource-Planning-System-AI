"""Strongly typed application settings loaded from environment / .env."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.constants import (
    DEFAULT_DATASET_CSV,
    DEFAULT_MODELS_DIR,
    JWT_ALGORITHM_DEFAULT,
    JWT_EXPIRE_MINUTES_DEFAULT,
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application
    app_name: str = "Restaurant Resource Planning System"
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    log_format: str = "text"  # text | json
    app_version: str = "1.0.0"

    # Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # CORS (comma-separated origins)
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174"

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/restaurant_rps"
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_recycle: int = 3600
    db_statement_timeout_seconds: int = 0
    # Prefer Alembic for schema; create_all only when explicitly allowed (tests)
    use_alembic: bool = True
    allow_create_all: bool = False

    # Seed policy — interview/demo: keep enterprise bootstrap ON.
    # Production empty catalog: set SEED_ENTERPRISE_DATA=false (users/RBAC still seed).
    seed_enterprise_data: bool = True
    seed_legacy_forecasts: bool = True

    # Paths (override in .env for deployments)
    models_dir: Path = Field(default_factory=lambda: DEFAULT_MODELS_DIR)
    dataset_csv_path: Path = Field(default_factory=lambda: DEFAULT_DATASET_CSV)

    # Security — JWT
    secret_key: str = "change-me-in-production-use-openssl-rand-hex-32"
    jwt_algorithm: str = JWT_ALGORITHM_DEFAULT
    jwt_expire_minutes: int = JWT_EXPIRE_MINUTES_DEFAULT
    jwt_access_expire_minutes: int = 30
    jwt_refresh_expire_days: int = 14
    password_min_length: int = 8
    password_require_upper: bool = True
    password_require_lower: bool = True
    password_require_digit: bool = True
    password_require_special: bool = True
    max_failed_login_attempts: int = 5
    account_lock_minutes: int = 30
    rate_limit_enabled: bool = False
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60

    # Security headers / CSRF / HTTPS
    security_headers_enabled: bool = True
    csp_enabled: bool = True
    csp_policy: str = (
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: blob: https:; font-src 'self' data:; "
        "connect-src 'self' http: https: ws: wss:; frame-ancestors 'none'; "
        "base-uri 'self'; form-action 'self'"
    )
    hsts_enabled: bool = False
    hsts_max_age_seconds: int = 31536000
    https_redirect_enabled: bool = False
    csrf_enabled: bool = False
    csrf_cookie_name: str = "csrf_token"
    csrf_header_name: str = "X-CSRF-Token"

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_enabled: bool = True
    redis_session_ttl_seconds: int = 86400
    redis_cache_default_ttl_seconds: int = 300
    redis_key_prefix: str = "rrps"

    # Celery / queue
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    celery_task_always_eager: bool = False
    celery_task_acks_late: bool = True
    celery_task_default_retry_delay: int = 60
    celery_task_max_retries: int = 3

    # Object storage
    storage_backend: str = "local"  # local | s3 | r2 | azure | gcs
    storage_local_root: Path = Field(default_factory=lambda: Path("uploads"))
    storage_public_base_url: str = "/uploads"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    s3_bucket: str = ""
    s3_endpoint_url: str = ""  # R2 / MinIO compatible
    azure_storage_connection_string: str = ""
    azure_storage_container: str = "uploads"
    gcs_bucket: str = ""
    gcs_credentials_json: str = ""

    # Observability
    sentry_dsn: str = ""
    sentry_traces_sample_rate: float = 0.1
    metrics_enabled: bool = True
    tracing_enabled: bool = True

    # Backups
    backup_dir: Path = Field(default_factory=lambda: Path("backups"))
    backup_retention_days: int = 14
    backup_verify_on_write: bool = True

    # Deployment metadata (surfaced in /platform/deployment)
    deployment_id: str = "local"
    deployment_region: str = "local"
    git_sha: str = "unknown"
    build_timestamp: str = ""

    @field_validator("database_url")
    @classmethod
    def require_postgresql(cls, value: str) -> str:
        if value.startswith("sqlite"):
            raise ValueError(
                "SQLite is not supported. Set DATABASE_URL to a PostgreSQL connection string."
            )
        if not value.startswith("postgresql"):
            raise ValueError("DATABASE_URL must use the postgresql:// scheme.")
        return value

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        return value.upper()

    @field_validator("log_format")
    @classmethod
    def normalize_log_format(cls, value: str) -> str:
        normalized = value.lower().strip()
        if normalized not in {"text", "json"}:
            raise ValueError("LOG_FORMAT must be 'text' or 'json'.")
        return normalized

    @field_validator("storage_backend")
    @classmethod
    def normalize_storage_backend(cls, value: str) -> str:
        normalized = value.lower().strip()
        allowed = {"local", "s3", "r2", "azure", "gcs"}
        if normalized not in allowed:
            raise ValueError(f"STORAGE_BACKEND must be one of {sorted(allowed)}")
        return normalized

    @field_validator("app_env")
    @classmethod
    def normalize_app_env(cls, value: str) -> str:
        return value.lower().strip()

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env in {"production", "prod"}

    @property
    def is_testing(self) -> bool:
        return self.app_env in {"test", "testing"}

    @property
    def effective_csp(self) -> str | None:
        if not self.csp_enabled:
            return None
        return self.csp_policy


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
