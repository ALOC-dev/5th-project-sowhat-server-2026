class AppError(Exception):
    """Base exception for application-specific errors."""

    default_message = "애플리케이션 오류가 발생했습니다."
    status_code = 500

    def __init__(self, message: str | None = None):
        self.message = message or self.default_message
        super().__init__(self.message)


class InfrastructureError(AppError):
    """Base exception for infrastructure-related errors."""

    default_message = "인프라 오류가 발생했습니다."
    status_code = 503


class DomainError(AppError):
    """Base exception for domain rule violations."""

    default_message = "도메인 오류가 발생했습니다."
    status_code = 400
