from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.schemas.profile import ProfileCreate, ProfileResponse
from app.crud.profiles import upsert_profile

router = APIRouter(prefix="/profiles", tags=["profiles"])


# ── POST /profiles ────────────────────────────────────────

@router.post("", response_model=ProfileResponse)
async def create_profile(payload: ProfileCreate, db: AsyncSession = Depends(get_db)):
    success = await upsert_profile(db, payload)
    return ProfileResponse(success=success)
