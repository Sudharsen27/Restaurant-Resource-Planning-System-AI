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

    # Paths (override in .env for deployments)
    models_dir: Path = Field(default_factory=lambda: DEFAULT_MODELS_DIR)
    dataset_csv_path: Path = Field(default_factory=lambda: DEFAULT_DATASET_CSV)

    # Security — JWT ready (not enforced on routes yet)
    secret_key: str = "change-me-in-production-use-openssl-rand-hex-32"
    jwt_algorithm: str = JWT_ALGORITHM_DEFAULT
    jwt_expire_minutes: int = JWT_EXPIRE_MINUTES_DEFAULT
    jwt_access_expire_minutes: int = 30
    jwt_refresh_expire_days: int = 14
    password_min_length: int = 8
    max_failed_login_attempts: int = 5
    account_lock_minutes: int = 30
    rate_limit_enabled: bool = False
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60

    # Security headers middleware
    security_headers_enabled: bool = True

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

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() in {"production", "prod"}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
