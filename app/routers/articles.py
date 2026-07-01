from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from datetime import datetime

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

def get_recommended_articles(db, user_id):

    user = user_crud.get_user_by_id(db, user_id)
    if user is None:
        raise UserNotFoundError()
        
    user_interests = personal_crud.get_user_interest_scores(db, user_id) or {}
    
    all_articles = article_crud.get_all_articles(db)
    scored_articles = []
    
    current_time = datetime.now()
    
    for article in all_articles:

        score = 0.0
        
        if article.keyword:
            article_keywords = [k.strip() for k in article.keyword.split(",")] if isinstance(article.keyword, str) else article.keyword
            for keyword in article_keywords:
                score += user_interests.get(keyword, 0) * 2.0  #자주 읽은 건 가중치 2.0
                
        if getattr(article, "created_at", None):
            time_delta = (current_time - article.created_at).total_seconds() / 3600 # 시간 단위

            if time_delta <= 24:
                score += 10.0
            elif time_delta <= 72:
                score += 5.0
                
        if getattr(article, "target_job", None) == user.job:
            score += 3.0
        if getattr(article, "target_region", None) == user.region:
            score += 2.0

        if getattr(article, "is_important", False):
            score += 5.0
            
        scored_articles.append((score, article))
        
    scored_articles.sort(key=lambda x: x[0], reverse=True)
    top_20_articles = [item[1] for item in scored_articles[:20]]
    
    for article in top_20_articles:
        if len(article.content) > 25:
            article.content = article.content[:25] + "..."
            
    return top_20_articles