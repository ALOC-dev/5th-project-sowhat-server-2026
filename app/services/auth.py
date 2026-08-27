import re
from fastapi import HTTPException, Request, Response, status
from jose import JWTError
from sqlalchemy.orm import Session

import app.crud.user as crud
from app.exceptions.security import AuthenticationError
from app.exceptions.validation import ValidationError
import app.services.user as user_service
from app.services.llm_service import filter_user_extra_information
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.exceptions.domain import DuplicateLoginIdError, UserNotFoundError
from app.models.user import User
from app.schemas.user import LoginRequest, SignupRequest


async def signup(db: Session, payload: SignupRequest) -> User:
    user_service._validate_create_user_payload(payload)

    if crud.exists_user_by_login_id(db, payload.login_id):
        raise DuplicateLoginIdError()

    user_data = payload.model_dump(exclude={"password"})
    user_data["hashed_password"] = hash_password(payload.password)

    # 사용자가 입력한 추가 정보는 그대로 쓰지 않고 개인화에 쓸 수 있게 필터링한다.
    # 이 값이 비면 개인해설 프롬프트의 '추가 정보' 입력도 빈 값이 된다.
    filtered = await filter_user_extra_information(payload.extra_information)
    user_data["filtered_extra_information"] = (
        user_service._validate_user_extra_information(filtered)
    )

    user = crud.create_user(db, user_data)
    return await user_service.attach_profile_embedding(db, user)


def login(db: Session, payload: LoginRequest, response: Response):
    user = crud.get_user_by_login_id(db, payload.login_id)

    if user is None or user.hashed_password is None:
        raise AuthenticationError("아이디 또는 비밀번호가 올바르지 않습니다.")

    if not verify_password(payload.password, user.hashed_password):
        raise AuthenticationError("아이디 또는 비밀번호가 올바르지 않습니다.")

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/api/auth/refresh",
    )

    return {
        "id": user.id,
        "message": "로그인에 성공했습니다.",
    }


def logout(response: Response):
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        path="/",
    )

    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        path="/api/auth/refresh",
    )

    return {"message": "로그아웃되었습니다."}


def get_current_user(db: Session, request: Request) -> User:
    token = request.cookies.get("access_token")

    if token is None:
        raise AuthenticationError()

    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")

        if user_id is None:
            raise AuthenticationError()

    except JWTError:
        raise AuthenticationError()

    user = crud.get_user_by_id(db, int(user_id))

    if user is None:
        raise UserNotFoundError()

    return user


def refresh(db: Session, request: Request, response: Response):
    token = request.cookies.get("refresh_token")

    if token is None:
        raise AuthenticationError()

    try:
        payload = decode_refresh_token(token)
        user_id = payload.get("sub")

        if user_id is None:
            raise AuthenticationError()

    except JWTError:
        raise AuthenticationError()

    user = crud.get_user_by_id(db, int(user_id))

    if user is None:
        raise UserNotFoundError()

    access_token = create_access_token(user.id)

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )

    return {"message": "access token이 재발급되었습니다."}


def verify_user(user: User, payload: dict[str, str]) -> dict[str, bool]:
    current_password = payload.get("password", None)
    if current_password is None:
        raise ValidationError("비밀번호가 올바르지 않습니다.")

    if not verify_password(current_password, user.hashed_password):
        raise AuthenticationError("비밀번호가 올바르지 않습니다.")

    return {"success": True}
