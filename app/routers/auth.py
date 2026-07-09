from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.user import LoginRequest, UserGetResponse
import app.services.auth as service

router = APIRouter(prefix="/api/auth", tags=["auth"])

# TODO:
#   로그인 로그아웃 구현 (민우오빠)


@router.post("/login")
def login(
    payload: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    return service.login(db, payload, response)


@router.post("/logout")
def logout(response: Response):
    return service.logout(response)

@router.get("/me", response_model=UserGetResponse)
def get_me(
    request: Request,
    db: Session = Depends(get_db),
):
    return service.get_current_user(db, request)


#   회원가입 구현 (지원언니)

@router.post("/signup")
def signup():
    pass
