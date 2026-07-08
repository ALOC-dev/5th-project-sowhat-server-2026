from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.user import *
import app.services.user as service

router = APIRouter(prefix="/api/users", tags=["users"])


# ── POST /api/users ────────────────────────────────────────
# 성공 시 응답: 201 CREATED
@router.post("", response_model=UserCreateResponse, status_code=201)
async def create_user(payload: UserCreateRequest, db: Session = Depends(get_db)):
    user = await service.create_user(db, payload)
    return user


# ── GET /api/users/{user_id} ─────────────────────────────────
@router.get("/{user_id}", response_model=UserGetResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    return service.get_user(db, user_id)


# ── PATCH /api/users/{user_id} ─────────────────────────────────
@router.patch("/{user_id}", response_model=UserUpdateResponse)
async def update_user(
    user_id: int, payload: UserUpdateRequest, db: Session = Depends(get_db)
):
    user = await service.update_user(db, user_id, payload)
    return user
