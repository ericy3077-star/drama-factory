"""Global custom exceptions and FastAPI exception handlers."""
from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse


# ── Domain exceptions ─────────────────────────────────────────────────────────


class AppError(Exception):
    """Base application error."""
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = "INTERNAL_ERROR"

    def __init__(self, detail: str = "An unexpected error occurred") -> None:
        self.detail = detail
        super().__init__(detail)


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "NOT_FOUND"

    def __init__(self, resource: str = "Resource") -> None:
        super().__init__(f"{resource} not found")


class UnauthorizedError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "UNAUTHORIZED"

    def __init__(self, detail: str = "Authentication required") -> None:
        super().__init__(detail)


class ForbiddenError(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "FORBIDDEN"

    def __init__(self, detail: str = "Insufficient permissions") -> None:
        super().__init__(detail)


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    error_code = "CONFLICT"


class RateLimitError(AppError):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    error_code = "RATE_LIMITED"

    def __init__(self, retry_after: int = 60) -> None:
        super().__init__(f"Rate limit exceeded. Retry after {retry_after}s")
        self.retry_after = retry_after


class ExternalServiceError(AppError):
    status_code = status.HTTP_502_BAD_GATEWAY
    error_code = "EXTERNAL_SERVICE_ERROR"


class QuotaExceededError(AppError):
    status_code = status.HTTP_402_PAYMENT_REQUIRED
    error_code = "QUOTA_EXCEEDED"

    def __init__(self, detail: str = "Usage quota exceeded for your plan") -> None:
        super().__init__(detail)


# ── Handler registration ──────────────────────────────────────────────────────


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> ORJSONResponse:
        content = {"error": exc.error_code, "detail": exc.detail}
        headers = {}
        if isinstance(exc, RateLimitError):
            headers["Retry-After"] = str(exc.retry_after)
        return ORJSONResponse(
            status_code=exc.status_code,
            content=content,
            headers=headers or None,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> ORJSONResponse:
        return ORJSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "VALIDATION_ERROR",
                "detail": exc.errors(),
            },
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception) -> ORJSONResponse:
        return ORJSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "INTERNAL_ERROR", "detail": "An unexpected error occurred"},
        )
