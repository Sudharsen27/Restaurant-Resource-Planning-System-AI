"""Application constants — paths and shared defaults (no secrets)."""

from pathlib import Path

# Backend package root: Backend/
BACKEND_ROOT = Path(__file__).resolve().parents[2]

# Artifact & data paths (overridable via Settings)
DEFAULT_MODELS_DIR = BACKEND_ROOT / "models"
DEFAULT_DATASET_DIR = BACKEND_ROOT / "dataset"
DEFAULT_DATASET_CSV = DEFAULT_DATASET_DIR / "restaurant_data.csv"

# API
API_V1_PREFIX = "/api/v1"
APP_VERSION = "1.0.0"

# Logging
LOG_FORMAT_JSON = "json"
LOG_FORMAT_TEXT = "text"

# Security placeholders (JWT-ready; auth not enforced yet)
JWT_ALGORITHM_DEFAULT = "HS256"
JWT_EXPIRE_MINUTES_DEFAULT = 60
