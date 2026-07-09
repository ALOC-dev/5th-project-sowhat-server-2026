from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.user import (
    LoginRequest,
    SignupRequest,
    UserCreateResponse,
    UserGetResponse,
)
import app.services.auth as service

router = APIRouter(prefix="/api/auth", tags=["auth"])


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

@router.post("/refresh")
def refresh(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    return service.refresh(db, request, response)


# ── POST /api/auth/signup ────────────────────────────────────
# 성공 시 응답: 201 CREATED (토큰 발급 없음, 로그인은 별도 진행)
@router.post("/signup", response_model=UserCreateResponse, status_code=201)
async def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    return await service.signup(db, payload)
