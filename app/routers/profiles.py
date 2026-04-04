from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.user import ProfileCreate, ProfileResponse
import app.services.user as service

router = APIRouter(prefix="/profiles", tags=["profiles"])


# ── POST /profiles ────────────────────────────────────────


@router.post("", response_model=ProfileResponse)
def create_profile(payload: ProfileCreate, db: Session = Depends(get_db)):
    success = service.create_profile(db, payload)
    return ProfileResponse(success=success)
