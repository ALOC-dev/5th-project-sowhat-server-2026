from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.user import SignupRequest, UserCreateResponse
import app.services.auth as service

router = APIRouter(prefix="/api/auth", tags=["auth"])

# TODO:
#   로그인 로그아웃 구현 (민우오빠)


@router.post("/login")
def login():
    pass


@router.post("/logout")
def logout():
    pass


# ── POST /api/auth/signup ────────────────────────────────────
# 성공 시 응답: 201 CREATED (토큰 발급 없음, 로그인은 별도 진행)
@router.post("/signup", response_model=UserCreateResponse, status_code=201)
async def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    return await service.signup(db, payload)
