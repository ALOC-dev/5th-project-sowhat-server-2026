# TODO:
#   로그인 로그아웃 구현 (민우오빠)

from fastapi import HTTPException, Request, Response, status
from jose import JWTError
from sqlalchemy.orm import Session

import app.crud.user as crud
from app.core.config import settings
from app.core.security import create_access_token, verify_password, decode_access_token
from app.models.user import User
from app.schemas.user import LoginRequest


def login(db: Session, payload: LoginRequest, response: Response):
    user = crud.get_user_by_email(db, payload.email)

    if user is None or user.hashed_password is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
        )

    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
        )

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

    return {
        "id": user.id,
        "message": "로그인에 성공했습니다.",
    }


def logout(response: Response):
    response.delete_cookie(
        key="access_token",
        path="/",
    )

    return {"message": "로그아웃되었습니다."}


def get_current_user(db: Session, request: Request) -> User:
    token = request.cookies.get("access_token")

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증되지 않은 사용자입니다.",
        )

    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 토큰입니다.",
            )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다.",
        )

    user = crud.get_user_by_id(db, int(user_id))

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자를 찾을 수 없습니다.",
        )

    return user


#   회원가입 구현 (지원언니)
