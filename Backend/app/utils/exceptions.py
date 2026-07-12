class AppException(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppException):
    def __init__(self, resource: str, resource_id: int) -> None:
        super().__init__(f"{resource} with id {resource_id} not found", status_code=404)


class ConflictError(AppException):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=409)


class ValidationError(AppException):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=422)
