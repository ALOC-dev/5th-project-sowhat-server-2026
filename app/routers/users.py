from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.user import *
import app.services.user as service
from app.exceptions import UserNotFoundError

router = APIRouter(prefix="/api/users", tags=["users"])


# ── POST /api/users ────────────────────────────────────────


# 성공 시 응답: 201 CREATED
@router.post("", response_model=UserCreateResponse, status_code=201)
def create_user(payload: UserCreateRequest, db: Session = Depends(get_db)):
    created_user = service.create_user(db, payload)
    return created_user


# ── GET /api/users/{user_id} ─────────────────────────────────


@router.get("/{user_id}", response_model=UserGetResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = service.get_user(db, user_id)
    if user is None:
        raise UserNotFoundError()
    return user


# ── PATCH /api/users/{user_id} ─────────────────────────────────


@router.patch("/{user_id}", response_model=UserUpdateResponse)
def modify_user(
    user_id: int, payload: UserUpdateRequest, db: Session = Depends(get_db)
):
    updated_user = service.modify_user(db, user_id, payload)
    if updated_user is None:
        raise UserNotFoundError()
    return updated_user
