from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db

from app.schemas.article import ArticleResponse, ArticleDetailResponse
from app.schemas.personal_analysis import PersonalAnalysis

import app.services.article as service

router = APIRouter(prefix="/api/articles", tags=["articles"])


# ── GET /articles ─────────────────────────────────────────


@router.get("", response_model=list[ArticleResponse])
def list_articles(
    db: Session = Depends(get_db),
):
    try:
        articles = service.get_all_articles(db)
        return articles
    except Exception as e:
        raise HTTPException(status_code=404, detail=e)


# ── GET /articles/analysis (순서 중요: /{article_id} 보다 위) ──


@router.get("/analysis", response_model=PersonalAnalysis)
def get_analysis(
    article_id: int = Query(...),
    user_id: int = Query(...),
    db: Session = Depends(get_db),
):
    try:
        analysis = service.get_personal_analysis(db, article_id, user_id)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=404, detail=e)


# ── GET /articles/{article_id} ────────────────────────────


@router.get("/{article_id}", response_model=ArticleDetailResponse)
def get_article(article_id: int, db: Session = Depends(get_db)):
    try:
        articleDetail = service.get_common_analysis(db, article_id)
        return articleDetail
    except Exception as e:
        raise HTTPException(status_code=404, detail=e)
