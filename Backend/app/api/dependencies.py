"""FastAPI dependencies — DB + auth guards."""

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.db.session import get_db
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.models import Permission, Role, User
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.services.auth_service import decode_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise UnauthorizedError("Authentication required")
    payload = decode_token(credentials.credentials)
    if payload.get("type") != "access":
        raise UnauthorizedError("Invalid access token")
    user_id = int(payload.get("sub", 0))
    user = db.get(User, user_id)
    if user is None or user.is_deleted or not user.is_active:
        raise UnauthorizedError("Invalid user")
    return user


def require_roles(*allowed_roles: str):
    def _dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.value not in allowed_roles:
            raise ForbiddenError("Insufficient role")
        return current_user

    return _dependency


def require_permission(permission_code: str):
    def _dependency(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        stmt = (
            select(Permission.code)
            .join(Role.permissions)
            .where(Role.name == current_user.role.value)
        )
        granted = set(db.scalars(stmt).all())
        if permission_code not in granted:
            raise ForbiddenError("Insufficient permission")
        return current_user

    return _dependency

def require_super_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role.value != "SUPER_ADMIN":
        raise ForbiddenError("Super admin access required")
    return current_user


__all__ = [
    "get_db",
    "get_current_user",
    "require_roles",
    "require_permission",
    "require_super_admin",
    "bearer_scheme",
]
