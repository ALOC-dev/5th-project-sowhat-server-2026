from app.exceptions.base import InfrastructureError


class DatabaseError(InfrastructureError):
    """Raised when database operations fail."""

    default_message = "데이터베이스 연결 실패"
    status_code = 503


class ExternalAPIError(InfrastructureError):
    """Raised when external API interactions fail."""

    default_message = "외부 API 호출 실패"
    status_code = 502


class CacheError(InfrastructureError):
    """Raised when cache operations fail."""

    default_message = "캐시 처리 실패"
    status_code = 503
