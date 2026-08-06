from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.article import ArticlePreviewResponse
from app.schemas.user import (
    UserCreateRequest,
    UserCreateResponse,
    UserGetResponse,
    UserUpdateRequest,
    UserUpdateResponse,
)
import app.services.article as article_service
import app.services.auth as auth_service
import app.services.user as service

router = APIRouter(prefix="/api/users", tags=["users"])


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
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    current_user = auth_service.get_current_user(db, request)
    user = await service.update_user(db, current_user.id, payload, background_tasks)
    return user


# ── GET /api/users/me/articles ──────────────────────────────
# 로그인한 사용자가 조회한 기사 목록을 최근 조회 순으로 반환
@router.get("/me/articles", response_model=list[ArticlePreviewResponse])
def get_my_viewed_articles(
    request: Request,
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    current_user = auth_service.get_current_user(db, request)
    return article_service.get_viewed_articles(db, current_user.id, limit, offset)
