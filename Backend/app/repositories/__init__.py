"""Repository package — data access only; no business logic."""

from app.repositories.forecast_repository import ForecastRepository
from app.repositories.prediction_repository import PredictionRepository

__all__ = ["ForecastRepository", "PredictionRepository"]
