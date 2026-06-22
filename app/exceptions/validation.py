from app.exceptions.base import AppError


class ValidationError(AppError):
    """Raised when input validation fails."""

    default_message = "요청값 검증에 실패했습니다."
    status_code = 422
