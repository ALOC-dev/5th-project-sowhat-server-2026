from fastapi import APIRouter, Depends, HTTPException, Query
from app.schemas.article import ArticleListItem
from app.services.article_service import list_articles as list_articles_service

router = APIRouter(prefix="/articles", tags=["articles"])


# ── GET /articles ─────────────────────────────────────────

@router.get("", response_model=list[ArticleListItem])
def list_articles():
    return list_articles_service()

