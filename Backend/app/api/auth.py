from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.api.dependencies import bearer_scheme, get_current_user, get_db
from app.models import User
from app.models.auth import UserSession
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    ResetPasswordRequest,
    SessionInfo,
)
from app.services.auth_service import (
    authenticate_user,
    change_password,
    create_password_reset_token,
    decode_token,
    get_active_sessions,
    logout,
    rotate_refresh_token,
    terminate_session,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


def _token_meta() -> dict:
    return {
        "token_type": "bearer",
        "expires_in": settings.jwt_access_expire_minutes * 60,
        "refresh_expires_in": settings.jwt_refresh_expire_days * 24 * 60 * 60,
    }

@router.post("/login")
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> dict:
    user, access_token, refresh_token, _session_id = authenticate_user(
        db,
        email=payload.email,
        password=payload.password,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    return {
        "success": True,
        "message": "Login successful",
        "data": {
            "user": {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "role": user.role.value,
                "email_verified": user.email_verified,
            },
            "tokens": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                **_token_meta(),
            },
        },
    }


@router.post("/refresh")
def refresh(payload: RefreshRequest, request: Request, db: Session = Depends(get_db)) -> dict:
    access_token, refresh_token = rotate_refresh_token(
        db,
        refresh_token=payload.refresh_token,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    return {
        "success": True,
        "message": "Token refreshed",
        "data": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            **_token_meta(),
        },
    }


@router.post("/logout")
def logout_endpoint(
    payload: LogoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    revoked = logout(
        db,
        user=current_user,
        refresh_token=payload.refresh_token,
        all_sessions=payload.all_sessions,
    )
    return {
        "success": True,
        "message": "Logout successful",
        "data": {"sessions_revoked": revoked},
    }


@router.get("/me")
def me(current_user: User = Depends(get_current_user)) -> dict:
    return {
        "success": True,
        "message": "Current user fetched",
        "data": {
            "id": current_user.id,
            "full_name": current_user.full_name,
            "email": current_user.email,
            "role": current_user.role.value,
            "email_verified": current_user.email_verified,
            "last_login_at": current_user.last_login_at,
        },
    }


@router.post("/change-password")
def change_password_endpoint(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    change_password(
        db,
        user=current_user,
        current_password=payload.current_password,
        new_password=payload.new_password,
    )
    return {"success": True, "message": "Password changed successfully", "data": None}


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)) -> dict:
    raw_token = create_password_reset_token(db, email=payload.email)
    return {
        "success": True,
        "message": "If the account exists, a reset token has been generated",
        "data": {"reset_token": raw_token},
    }


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)) -> dict:
    from app.services.auth_service import reset_password

    reset_password(db, token=payload.token, new_password=payload.new_password)
    return {"success": True, "message": "Password reset successful", "data": None}


def _current_session_id(credentials: HTTPAuthorizationCredentials | None) -> int | None:
    if not credentials:
        return None
    try:
        sid = decode_token(credentials.credentials).get("sid")
        return int(sid) if sid is not None else None
    except Exception:
        return None


@router.get("/sessions")
def list_sessions(
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> dict:
    current_sid = _current_session_id(credentials)
    sessions = get_active_sessions(db, user_id=current_user.id)
    data = []
    for s in sessions:
        info = SessionInfo.model_validate(s).model_dump(mode="json")
        info["is_current"] = bool(current_sid is not None and s.id == current_sid)
        info["os"] = s.operating_system
        data.append(info)
    return {"success": True, "message": "Active sessions", "data": data}


@router.post("/sessions/revoke-others")
def revoke_other_sessions(
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> dict:
    current_sid = _current_session_id(credentials)
    now = datetime.now(timezone.utc)
    sessions = db.scalars(
        select(UserSession).where(
            UserSession.user_id == current_user.id,
            UserSession.revoked.is_(False),
        )
    ).all()
    revoked = 0
    for session in sessions:
        if current_sid is not None and session.id == current_sid:
            continue
        session.revoked = True
        session.logged_out_at = now
        revoked += 1
    db.commit()
    return {
        "success": True,
        "message": "Other sessions terminated",
        "data": {"sessions_revoked": revoked},
    }


@router.delete("/sessions/{session_id}")
def revoke_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    terminate_session(db, user_id=current_user.id, session_id=session_id)
    return {"success": True, "message": "Session terminated", "data": None}
