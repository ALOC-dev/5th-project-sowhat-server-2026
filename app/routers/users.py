from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.personal_analysis import ViewedArticleResponse
from app.schemas.user import (
    UserGetResponse,
    UserUpdateRequest,
    UserUpdateResponse,
)
import app.services.article as article_service
import app.services.auth as auth_service
import app.services.user as user_service

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
    user = await user_service.update_user(
        db, current_user.id, payload, background_tasks
    )
    return user


# ── PATCH /api/users/me/password ────────────────────────────
# 비밀번호 변경
@router.patch("/me/password", response_model=dict[str, bool])
def update_my_password(
    payload: dict[str, str], request: Request, db: Session = Depends(get_db)
):
    current_user = auth_service.get_current_user(db, request)
    return user_service.update_user_password(db, current_user.id, payload)


# ── GET /api/users/me/articles ──────────────────────────────
# 로그인한 사용자가 조회한 기사 목록을 최근 조회 순으로 반환
@router.get("/me/articles", response_model=list[ViewedArticleResponse])
def get_my_viewed_articles(
    request: Request,
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    current_user = auth_service.get_current_user(db, request)
    return article_service.get_viewed_articles(db, current_user.id, limit, offset)


# GET /api/users/me/helpful-analyses
@router.get("/me/helpful-analyses", response_model=list[ViewedArticleResponse])
def get_my_helpful_analyses(
    request: Request,
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    current_user = auth_service.get_current_user(db, request)
    return article_service.get_helpful_analyses(db, current_user.id, limit, offset)


# ── POST /api/users/check-id ──────────────────────────────
# 중복 login_id가 있는지 조회
@router.post("/check-id", response_model=dict[str, bool])
def check_duplicate_id(payload: dict[str, str], db: Session = Depends(get_db)):
    return user_service.check_duplicate_id(db, payload)
