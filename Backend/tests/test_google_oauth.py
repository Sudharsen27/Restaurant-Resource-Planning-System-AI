from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.services import auth_service


def test_google_login_rejects_when_not_configured(monkeypatch):
    monkeypatch.setattr(auth_service.settings, "google_oauth_client_id", "")

    try:
        auth_service.authenticate_google_user(
            db=Mock(),
            id_token="header.payload.sig",
            ip_address="127.0.0.1",
            user_agent="pytest",
        )
        raise AssertionError("Expected ForbiddenError")
    except ForbiddenError as exc:
        assert "not configured" in str(exc).lower()


def test_google_login_links_existing_user_by_email(monkeypatch):
    user = SimpleNamespace(
        id=7,
        email="chef@example.com",
        full_name="Chef",
        role=SimpleNamespace(value="ADMIN"),
        email_verified=False,
        auth_provider="local",
        google_sub=None,
        is_active=True,
        is_deleted=False,
        locked_until=None,
        failed_login_attempts=3,
        last_login_at=None,
    )
    db = Mock()
    db.scalar = Mock(side_effect=[None, user])
    db.add = Mock()
    db.flush = Mock()
    db.commit = Mock()

    monkeypatch.setattr(
        auth_service.settings,
        "google_oauth_client_id",
        "test-client.apps.googleusercontent.com",
    )
    monkeypatch.setattr(auth_service.settings, "google_oauth_allow_signup", False)
    monkeypatch.setattr(
        auth_service,
        "_verify_google_id_token",
        Mock(
            return_value={
                "sub": "google-sub-1",
                "email": "chef@example.com",
                "email_verified": True,
                "name": "Chef",
                "iss": "https://accounts.google.com",
            }
        ),
    )
    monkeypatch.setattr(auth_service, "_get_user_permissions", Mock(return_value=["products:read"]))
    monkeypatch.setattr(
        auth_service,
        "_create_jwt_token",
        Mock(side_effect=["access-token", "refresh-token"]),
    )

    session = SimpleNamespace(id=99, refresh_token_hash="pending")
    with patch("app.services.auth_service.UserSession", return_value=session):
        result_user, access, refresh, session_id = auth_service.authenticate_google_user(
            db,
            id_token="valid.google.token",
            ip_address="127.0.0.1",
            user_agent="pytest",
        )

    assert result_user is user
    assert user.google_sub == "google-sub-1"
    assert user.email_verified is True
    assert user.auth_provider == "google"
    assert access == "access-token"
    assert refresh == "refresh-token"
    assert session_id == 99
    db.commit.assert_called()


def test_google_login_blocks_unknown_email_without_signup(monkeypatch):
    db = Mock()
    db.scalar = Mock(return_value=None)

    monkeypatch.setattr(
        auth_service.settings,
        "google_oauth_client_id",
        "test-client.apps.googleusercontent.com",
    )
    monkeypatch.setattr(auth_service.settings, "google_oauth_allow_signup", False)
    monkeypatch.setattr(
        auth_service,
        "_verify_google_id_token",
        Mock(
            return_value={
                "sub": "google-sub-2",
                "email": "unknown@example.com",
                "email_verified": True,
                "name": "Unknown",
                "iss": "https://accounts.google.com",
            }
        ),
    )

    try:
        auth_service.authenticate_google_user(
            db,
            id_token="valid.google.token",
            ip_address="127.0.0.1",
            user_agent="pytest",
        )
        raise AssertionError("Expected UnauthorizedError")
    except UnauthorizedError as exc:
        assert "no account" in str(exc).lower()
