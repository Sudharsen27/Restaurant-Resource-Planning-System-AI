"""Application exception hierarchy."""

from typing import Any


class AppException(Exception):
    """Base application error with HTTP status and optional field errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        errors: list[Any] | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.errors = errors or []
        super().__init__(message)


class NotFoundError(AppException):
    def __init__(self, resource: str, resource_id: Any = None) -> None:
        if resource_id is None:
            message = f"{resource} not found"
        else:
            message = f"{resource} with id {resource_id} not found"
        super().__init__(message, status_code=404)


class ConflictError(AppException):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=409)


class ValidationError(AppException):
    def __init__(self, message: str, errors: list[Any] | None = None) -> None:
        super().__init__(message, status_code=422, errors=errors)


class UnauthorizedError(AppException):
    """JWT-ready; not raised by routes until auth is enabled."""

    def __init__(self, message: str = "Unauthorized") -> None:
        super().__init__(message, status_code=401)


class ForbiddenError(AppException):
    def __init__(self, message: str = "Forbidden") -> None:
        super().__init__(message, status_code=403)


class RateLimitError(AppException):
    """Rate-limit ready; middleware can raise when enabled."""

    def __init__(self, message: str = "Rate limit exceeded") -> None:
        super().__init__(message, status_code=429)
