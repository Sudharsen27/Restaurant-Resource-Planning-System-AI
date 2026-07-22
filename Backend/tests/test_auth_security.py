"""Auth / security hardening unit tests."""

from app.core.security import generate_csrf_token, security_headers
from app.services.auth_service import validate_password_strength


def test_password_policy_rejects_weak():
    try:
        validate_password_strength("short")
        raised = False
    except Exception:
        raised = True
    assert raised


def test_password_policy_accepts_strong():
    validate_password_strength("Str0ng!Pass")


def test_security_headers_include_csp():
    headers = security_headers()
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    assert "Content-Security-Policy" in headers


def test_csrf_token_entropy():
    a = generate_csrf_token()
    b = generate_csrf_token()
    assert a != b
    assert len(a) >= 32
