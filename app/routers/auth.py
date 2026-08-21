from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.user import (
    LoginRequest,
    SignupRequest,
    UserCreateResponse,
)
import app.services.auth as service

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ── POST /api/auth/login ────────────────────────────────────
@router.post("/login")
def login(
    payload: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    return service.login(db, payload, response)


# ── POST /api/auth/logout ────────────────────────────────────
@router.post("/logout")
def logout(response: Response):
    return service.logout(response)


# ── POST /api/auth/refresh ────────────────────────────────────
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


# ── POST /api/auth/verifications ───────────────────────────
# 회원 탈퇴/비밀번호 변경 시
@router.post("/verifications")
async def verify_user(
    request: Request,
    payload: dict[str, str],
    db: Session = Depends(get_db),
):
    current_user = service.get_current_user(db, request)
    return service.verify_user(current_user, payload)
