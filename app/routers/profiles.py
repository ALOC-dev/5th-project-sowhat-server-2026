from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.profile import ProfileCreate, ProfileResponse
from app.crud.profiles import upsert_profile

router = APIRouter(prefix="/profiles", tags=["profiles"])


# ── POST /profiles ────────────────────────────────────────

@router.post("", response_model=ProfileResponse)
def create_profile(payload: ProfileCreate, db: Session = Depends(get_db)):
    success = upsert_profile(db, payload)
    return ProfileResponse(success=success)
