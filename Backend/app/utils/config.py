from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Restaurant Resource Planning System"
    app_env: str = "development"
    debug: bool = True

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    cors_origins: str = "http://localhost:5173"

    database_url: str = "postgresql://postgres:postgres@localhost:5432/restaurant_rps"

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

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
