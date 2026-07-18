"""Top-level API router — mounts /api/v1 and legacy root paths."""

from fastapi import APIRouter

from app.api.v1.router import v1_router
from app.core.constants import API_V1_PREFIX

api_router = APIRouter()

# Canonical versioned API
api_router.include_router(v1_router, prefix=API_V1_PREFIX)

# Legacy root paths (backward compatible with existing frontend)
api_router.include_router(v1_router)
