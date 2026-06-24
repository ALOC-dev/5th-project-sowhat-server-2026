import logging

from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.exceptions.exceptions import AppError

logger = logging.getLogger(__name__)


def _error_response(status_code: int, message: str, error_code: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": error_code,
                "message": message,
            },
        },
    )


async def app_error_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, AppError):
        return await unhandled_exception_handler(request, exc)

    return _error_response(
        status_code=exc.status_code,
        message=exc.message,
        error_code=exc.__class__.__name__,
    )


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, HTTPException):
        return await unhandled_exception_handler(request, exc)

    return _error_response(
        status_code=exc.status_code,
        message=str(exc.detail),
        error_code=exc.__class__.__name__,
    )


async def request_validation_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    if not isinstance(exc, RequestValidationError):
        return await unhandled_exception_handler(request, exc)

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {
                "code": "RequestValidationError",
                "message": "요청값 검증에 실패했습니다.",
                "details": exc.errors(),
            },
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception occurred", exc_info=exc)
    return _error_response(
        status_code=500,
        message="서버 내부 오류가 발생했습니다.",
        error_code="InternalServerError",
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(
        RequestValidationError,
        request_validation_exception_handler,
    )
    app.add_exception_handler(Exception, unhandled_exception_handler)
