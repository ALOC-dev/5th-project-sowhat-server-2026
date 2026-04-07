from fastapi import APIRouter, Depends, HTTPException, Query
from app.schemas.article import ArticleListItem
from app.services.llm_service import analyze_article_with_groq
from app.services.article_service import list_articles as list_articles_service
from app.schemas.analysis import ArticleAnalysis
from app.crud.articles import get_article_by_id

router = APIRouter(prefix="/articles", tags=["articles"])


# ── GET /articles ─────────────────────────────────────────

@router.get("", response_model=list[ArticleListItem])
def list_articles():
    return list_articles_service()

@router.post("/{article_id}/analyze", response_model=ArticleAnalysis)
async def analyze_article(article_id: int):
    article = get_article_by_id(article_id)

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    try:
        result = await analyze_article_with_groq(
            title=article["title"],
            content=article["content"],
            category=article["category"]
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))