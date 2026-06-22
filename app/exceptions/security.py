from app.exceptions.base import AppError


class AuthenticationError(AppError):
    """Raised when authentication fails."""

    default_message = "인증에 실패했습니다."
    status_code = 401


class AuthorizationError(AppError):
    """Raised when authorization fails."""

    default_message = "권한이 없습니다."
    status_code = 403
