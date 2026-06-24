from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db

from app.schemas.article import ArticlePreviewResponse, ArticleDetailResponse
from app.schemas.personal_analysis import PersonalAnalysis

import app.services.article as service

router = APIRouter(prefix="/api/articles", tags=["articles"])


# ── GET /articles ─────────────────────────────────────────
@router.get("", response_model=list[ArticlePreviewResponse])
def list_articles(
    db: Session = Depends(get_db),
):
    return service.get_all_articles(db)


# ── GET /articles/analysis (순서 중요: /{article_id} 보다 위) ──
@router.get("/analysis", response_model=PersonalAnalysis)
async def get_analysis(
    article_id: int = Query(alias="article-id"),
    user_id: int = Query(alias="user-id"),
    db: Session = Depends(get_db),
):
    analysis = await service.get_personal_analysis(db, article_id, user_id)
    return analysis


# ── GET /articles/{article_id} ────────────────────────────
@router.get("/{article_id}", response_model=ArticleDetailResponse)
async def get_article(article_id: int, db: Session = Depends(get_db)):
    article_detail = await service.get_common_analysis(db, article_id)
    return article_detail
