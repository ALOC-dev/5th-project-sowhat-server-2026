from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.user import (
    UserCreateRequest,
    UserCreateResponse,
    UserGetResponse,
    UserUpdateRequest,
    UserUpdateResponse,
)
import app.services.auth as auth_service
import app.services.user as service

router = APIRouter(prefix="/api/users", tags=["users"])


# ── POST /api/users ────────────────────────────────────────
# 성공 시 응답: 201 CREATED
@router.post("", response_model=UserCreateResponse, status_code=201)
async def create_user(payload: UserCreateRequest, db: Session = Depends(get_db)):
    return await service.create_user(db, payload)


# ── GET /api/users/me ───────────────────────────────────────
@router.get("/me", response_model=UserGetResponse)
def get_my_profile(
    request: Request,
    db: Session = Depends(get_db),
):
    current_user = auth_service.get_current_user(db, request)
    return current_user


# ── PATCH /api/users/me ─────────────────────────────────────
@router.patch("/me", response_model=UserUpdateResponse)
async def update_my_profile(
    payload: UserUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    current_user = auth_service.get_current_user(db, request)
    user = await service.update_user(db, current_user.id, payload)
    return user