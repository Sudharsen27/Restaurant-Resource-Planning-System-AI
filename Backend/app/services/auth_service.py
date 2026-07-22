from __future__ import annotations

import hashlib
import re
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from sqlalchemy import and_, delete, func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ForbiddenError, UnauthorizedError, ValidationError
from app.models import AuditLog, Permission, Role, User
from app.models.auth import EmailVerificationToken, PasswordHistory, PasswordResetToken, UserSession
from app.models.enums import AuditAction


def _now() -> datetime:
    return datetime.now(timezone.utc)


def hash_password(password: str) -> str:
    """Hash with bcrypt directly (passlib is incompatible with bcrypt>=4.1)."""
    secret = password.encode("utf-8")
    # bcrypt hard-limits to 72 bytes
    if len(secret) > 72:
        secret = secret[:72]
    return bcrypt.hashpw(secret, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        secret = plain_password.encode("utf-8")
        if len(secret) > 72:
            secret = secret[:72]
        return bcrypt.checkpw(secret, hashed_password.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def validate_password_strength(password: str) -> None:
    if len(password) < settings.password_min_length:
        raise ValidationError(
            f"Password must be at least {settings.password_min_length} characters long"
        )
    checks = [
        (r"[A-Z]", "Password must contain at least one uppercase letter"),
        (r"[a-z]", "Password must contain at least one lowercase letter"),
        (r"\d", "Password must contain at least one number"),
        (r"[^A-Za-z0-9]", "Password must contain at least one special character"),
    ]
    for pattern, message in checks:
        if not re.search(pattern, password):
            raise ValidationError(message)


def _create_jwt_token(
    *,
    user: User,
    token_type: str,
    expires_delta: timedelta,
    permissions: list[str] | None = None,
    session_id: int | None = None,
) -> str:
    now = _now()
    payload = {
        "sub": str(user.id),
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "jti": secrets.token_urlsafe(16),
        "role": user.role.value,
        "permissions": permissions or [],
    }
    if session_id is not None:
        payload["sid"] = session_id
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("Invalid or expired token") from exc


def _get_user_permissions(db: Session, user: User) -> list[str]:
    stmt = (
        select(Permission.code)
        .join(Role.permissions)
        .where(Role.name == user.role.value)
        .order_by(Permission.code)
    )
    return [row for row in db.scalars(stmt).all()]


def _audit(
    db: Session,
    *,
    action: AuditAction,
    actor_user_id: int | None,
    entity_type: str,
    entity_id: str | None,
    details: dict | None = None,
    ip_address: str | None = None,
) -> None:
    db.add(
        AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            ip_address=ip_address,
        )
    )


def _parse_user_agent(user_agent: str | None) -> tuple[str | None, str | None, str | None]:
    if not user_agent:
        return None, None, None
    ua = user_agent.lower()
    os_name = "Windows" if "windows" in ua else "Linux" if "linux" in ua else "macOS" if "mac" in ua else "Unknown"
    browser = "Chrome" if "chrome" in ua else "Firefox" if "firefox" in ua else "Edge" if "edg" in ua else "Unknown"
    device = "Mobile" if "mobile" in ua else "Desktop"
    return device, os_name, browser


def authenticate_user(
    db: Session,
    *,
    email: str,
    password: str,
    ip_address: str | None,
    user_agent: str | None,
) -> tuple[User, str, str, int]:
    user = db.scalar(select(User).where(and_(User.email == email, User.is_deleted.is_(False))))
    if user is None:
        raise UnauthorizedError("Invalid email or password")

    now = _now()
    if user.locked_until and user.locked_until > now:
        raise ForbiddenError("Account is temporarily locked. Try again later.")
    if not user.is_active:
        raise ForbiddenError("Account is inactive")

    if not verify_password(password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= settings.max_failed_login_attempts:
            user.locked_until = now + timedelta(minutes=settings.account_lock_minutes)
        _audit(
            db,
            action=AuditAction.LOGIN,
            actor_user_id=user.id,
            entity_type="auth",
            entity_id=str(user.id),
            details={"success": False, "reason": "invalid_password"},
            ip_address=ip_address,
        )
        db.commit()
        raise UnauthorizedError("Invalid email or password")

    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = now

    permissions = _get_user_permissions(db, user)
    device, os_name, browser = _parse_user_agent(user_agent)

    session = UserSession(
        user_id=user.id,
        refresh_token_hash="pending",
        ip_address=ip_address,
        user_agent=user_agent,
        device=device,
        operating_system=os_name,
        browser=browser,
        last_activity_at=now,
    )
    db.add(session)
    db.flush()

    access_token = _create_jwt_token(
        user=user,
        token_type="access",
        expires_delta=timedelta(minutes=settings.jwt_access_expire_minutes),
        permissions=permissions,
        session_id=session.id,
    )
    refresh_token = _create_jwt_token(
        user=user,
        token_type="refresh",
        expires_delta=timedelta(days=settings.jwt_refresh_expire_days),
        permissions=permissions,
        session_id=session.id,
    )
    # Store hash of the JWT refresh token (must match rotate_refresh_token)
    session.refresh_token_hash = _hash_token(refresh_token)

    _audit(
        db,
        action=AuditAction.LOGIN,
        actor_user_id=user.id,
        entity_type="auth",
        entity_id=str(user.id),
        details={"success": True, "session_id": session.id},
        ip_address=ip_address,
    )
    db.commit()
    return user, access_token, refresh_token, session.id


def rotate_refresh_token(
    db: Session,
    *,
    refresh_token: str,
    ip_address: str | None,
    user_agent: str | None,
) -> tuple[str, str]:
    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise UnauthorizedError("Invalid token type")

    user_id = int(payload["sub"])
    session_id = payload.get("sid")
    user = db.get(User, user_id)
    if user is None or user.is_deleted or not user.is_active:
        raise UnauthorizedError("Invalid session")

    session = db.get(UserSession, session_id) if session_id else None
    if session is None or session.revoked or session.logged_out_at is not None:
        raise UnauthorizedError("Session is no longer active")

    token_hash = _hash_token(refresh_token)
    if session.refresh_token_hash != token_hash:
        session.revoked = True
        session.logged_out_at = _now()
        db.commit()
        raise UnauthorizedError("Refresh token was rotated or revoked")

    permissions = _get_user_permissions(db, user)
    # Rotate: issue new JWT refresh and store its hash
    new_refresh_jwt = _create_jwt_token(
        user=user,
        token_type="refresh",
        expires_delta=timedelta(days=settings.jwt_refresh_expire_days),
        permissions=permissions,
        session_id=session.id,
    )
    session.refresh_token_hash = _hash_token(new_refresh_jwt)
    session.last_activity_at = _now()
    session.ip_address = ip_address or session.ip_address
    session.user_agent = user_agent or session.user_agent

    access_token = _create_jwt_token(
        user=user,
        token_type="access",
        expires_delta=timedelta(minutes=settings.jwt_access_expire_minutes),
        permissions=permissions,
        session_id=session.id,
    )
    db.commit()
    return access_token, new_refresh_jwt


def logout(
    db: Session,
    *,
    user: User,
    refresh_token: str | None = None,
    all_sessions: bool = False,
) -> int:
    now = _now()
    affected = 0
    if all_sessions:
        sessions = db.scalars(
            select(UserSession).where(
                UserSession.user_id == user.id,
                UserSession.revoked.is_(False),
            )
        ).all()
        for session in sessions:
            session.revoked = True
            session.logged_out_at = now
            affected += 1
    elif refresh_token:
        payload = decode_token(refresh_token)
        sid = payload.get("sid")
        session = db.get(UserSession, sid) if sid else None
        if session and session.user_id == user.id and not session.revoked:
            session.revoked = True
            session.logged_out_at = now
            affected = 1
    _audit(
        db,
        action=AuditAction.LOGOUT,
        actor_user_id=user.id,
        entity_type="auth",
        entity_id=str(user.id),
        details={"sessions_revoked": affected},
    )
    db.commit()
    return affected


def change_password(db: Session, *, user: User, current_password: str, new_password: str) -> None:
    if not verify_password(current_password, user.password_hash):
        raise UnauthorizedError("Current password is incorrect")
    validate_password_strength(new_password)

    recent_hashes = db.scalars(
        select(PasswordHistory.password_hash)
        .where(PasswordHistory.user_id == user.id)
        .order_by(PasswordHistory.created_at.desc())
        .limit(5)
    ).all()
    for old_hash in recent_hashes + [user.password_hash]:
        if verify_password(new_password, old_hash):
            raise ValidationError("New password must not match recently used passwords")

    db.add(PasswordHistory(user_id=user.id, password_hash=user.password_hash))
    user.password_hash = hash_password(new_password)
    user.password_changed_at = _now()
    _audit(
        db,
        action=AuditAction.UPDATE,
        actor_user_id=user.id,
        entity_type="password",
        entity_id=str(user.id),
        details={"event": "change_password"},
    )
    db.commit()


def create_password_reset_token(db: Session, *, email: str) -> str:
    user = db.scalar(select(User).where(and_(User.email == email, User.is_deleted.is_(False))))
    if user is None:
        # do not leak account existence
        return "If an account exists, password reset instructions were generated."

    raw = secrets.token_urlsafe(48)
    token_hash = _hash_token(raw)
    expires_at = _now() + timedelta(minutes=30)
    db.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
    )
    _audit(
        db,
        action=AuditAction.UPDATE,
        actor_user_id=user.id,
        entity_type="password",
        entity_id=str(user.id),
        details={"event": "forgot_password"},
    )
    db.commit()
    return raw


def reset_password(db: Session, *, token: str, new_password: str) -> None:
    validate_password_strength(new_password)
    token_hash = _hash_token(token)
    rec = db.scalar(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > _now(),
        )
    )
    if rec is None:
        raise UnauthorizedError("Invalid or expired reset token")

    user = db.get(User, rec.user_id)
    if user is None:
        raise UnauthorizedError("Invalid reset token")

    db.add(PasswordHistory(user_id=user.id, password_hash=user.password_hash))
    user.password_hash = hash_password(new_password)
    user.password_changed_at = _now()
    rec.used_at = _now()
    _audit(
        db,
        action=AuditAction.UPDATE,
        actor_user_id=user.id,
        entity_type="password",
        entity_id=str(user.id),
        details={"event": "reset_password"},
    )
    db.commit()


def get_active_sessions(db: Session, *, user_id: int) -> list[UserSession]:
    return db.scalars(
        select(UserSession)
        .where(
            UserSession.user_id == user_id,
            UserSession.revoked.is_(False),
            UserSession.logged_out_at.is_(None),
        )
        .order_by(UserSession.last_activity_at.desc())
    ).all()


def terminate_session(db: Session, *, user_id: int, session_id: int) -> None:
    session = db.get(UserSession, session_id)
    if session is None or session.user_id != user_id:
        raise UnauthorizedError("Session not found")
    session.revoked = True
    session.logged_out_at = _now()
    db.commit()
