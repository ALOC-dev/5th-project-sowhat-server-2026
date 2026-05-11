from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.user import *
import app.services.user as service
from app.exceptions import UserNotFoundError

router = APIRouter(prefix="/api/profiles", tags=["profiles"])


# ── POST /profiles ────────────────────────────────────────


# 성공 시 응답: 201 CREATED
@router.post("", response_model=ProfileCreateResponse, status_code=201)
def create_profile(payload: ProfileCreateRequest, db: Session = Depends(get_db)):
    created_profile = service.create_profile(db, payload)
    return created_profile


# ── GET /profiles/{user_id} ─────────────────────────────────


@router.get("/{user_id}", response_model=ProfileGetResponse)
def get_profile(user_id: int, db: Session = Depends(get_db)):
    profile = service.get_profile(db, user_id)
    if profile is None:
        raise UserNotFoundError()
    return profile


# ── PUT /profiles/{user_id} ─────────────────────────────────


@router.patch("/{user_id}", response_model=ProfileUpdateResponse)
def modify_profile(
    user_id: int, payload: ProfileUpdateRequest, db: Session = Depends(get_db)
):
    updated_profile = service.modify_profile(db, user_id, payload)
    if updated_profile is None:
        raise UserNotFoundError()
    return updated_profile
