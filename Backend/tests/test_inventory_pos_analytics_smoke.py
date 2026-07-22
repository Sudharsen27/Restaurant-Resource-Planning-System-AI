"""Additional domain API smoke tests — auth helpers & schemas."""

from app.core.security import create_access_token, decode_access_token
from app.core.config import settings


def test_jwt_roundtrip():
    token = create_access_token("42", expires_minutes=5, extra_claims={"role": "ADMIN"})
    payload = decode_access_token(token)
    assert payload["sub"] == "42"
    assert payload["role"] == "ADMIN"


def test_settings_production_flag():
    assert settings.app_env in {"development", "testing", "staging", "production", "prod", "test"}
