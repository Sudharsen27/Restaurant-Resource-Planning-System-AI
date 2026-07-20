from __future__ import annotations

from datetime import datetime, timezone

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.db.session import SessionLocal
from app.models.auth import UserSession
from app.services.auth_service import decode_token


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Decode bearer token, attach auth context, and update session activity."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request.state.user_id = None
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            token = auth_header.split(" ", 1)[1].strip()
            try:
                payload = decode_token(token)
                request.state.user_id = int(payload.get("sub"))
                sid = payload.get("sid")
                if sid and payload.get("type") in {"access", "refresh"}:
                    db = SessionLocal()
                    try:
                        session = db.get(UserSession, int(sid))
                        if session and not session.revoked and session.logged_out_at is None:
                            session.last_activity_at = datetime.now(timezone.utc)
                            db.commit()
                    finally:
                        db.close()
            except Exception:
                # auth is enforced in dependencies; middleware remains non-blocking
                pass

        return await call_next(request)
