from app.exceptions.base import DomainError


class UserNotFoundError(DomainError):
    """Raised when a user cannot be found."""

    default_message = "사용자를 찾을 수 없습니다."
    status_code = 404


class ArticleNotFoundError(DomainError):
    """Raised when an article cannot be found."""

    default_message = "기사를 찾을 수 없습니다."
    status_code = 404


class InvalidArgumentError(DomainError):
    """Raised when a domain argument is invalid."""

    default_message = "잘못된 입력값입니다."
    status_code = 400


class DuplicateArticleError(DomainError):
    """Raised when an article already exists."""

    default_message = "이미 존재하는 기사입니다."
    status_code = 409


class DuplicateLoginIdError(DomainError):
    """Raised when the email is already registered."""

    default_message = "이미 가입된 ID입니다."
    status_code = 409
