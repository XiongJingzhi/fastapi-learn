from typing import Any


class AppException(Exception):
    """Base application exception for service/domain layers."""

    def __init__(
        self,
        *,
        status_code: int,
        detail: str,
        error_code: str = "APP_ERROR",
        extra: dict[str, Any] | None = None,
    ) -> None:
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code
        self.extra = extra or {}
        super().__init__(detail)


class ResourceNotFoundError(AppException):
    def __init__(self, resource: str, identifier: Any) -> None:
        super().__init__(
            status_code=404,
            detail=f"{resource} not found",
            error_code=f"{resource.upper()}_NOT_FOUND",
            extra={"resource": resource, "identifier": str(identifier)},
        )


class PermissionDeniedError(AppException):
    def __init__(self, detail: str = "Not enough permissions") -> None:
        super().__init__(
            status_code=403,
            detail=detail,
            error_code="PERMISSION_DENIED",
        )


class BadRequestError(AppException):
    def __init__(self, detail: str, error_code: str = "BAD_REQUEST") -> None:
        super().__init__(
            status_code=400,
            detail=detail,
            error_code=error_code,
        )


class UnauthorizedError(AppException):
    def __init__(self, detail: str = "Could not validate credentials") -> None:
        super().__init__(
            status_code=401,
            detail=detail,
            error_code="UNAUTHORIZED",
        )


class ConflictError(AppException):
    def __init__(self, detail: str, error_code: str = "CONFLICT") -> None:
        super().__init__(
            status_code=409,
            detail=detail,
            error_code=error_code,
        )
