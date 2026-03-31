from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.schemas.article import ArticleListItem, ArticleDetail, ArticleAnalysis
from app.crud.articles import (
    get_articles,
    get_article_by_id,
    get_common_analysis,
)
from app.crud.profiles import get_user_by_id
from app.crud.analyses import get_personal_analysis, create_personal_analysis
from app.core.llm import generate_analysis
from app.crud.articles import make_preview

router = APIRouter(prefix="/articles", tags=["articles"])


# ── GET /articles ─────────────────────────────────────────

@router.get("", response_model=list[ArticleListItem])
async def list_articles(
    category: str | None = Query(None, description="economy | politics | society"),
    db: AsyncSession = Depends(get_db),
):
    articles = await get_articles(db, category=category)
    return [
        ArticleListItem(
            article_id=a.article_id,
            title=a.title,
            date=a.date,
            content_preview=make_preview(a.content),
            category=a.category.value,
        )
        for a in articles
    ]


# ── GET /articles/analysis (순서 중요: {article_id} 보다 위에 위치) ──

@router.get("/analysis", response_model=ArticleAnalysis)
async def get_analysis(
    article_id: int = Query(...),
    user_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
):
    # 기사 존재 확인
    article = await get_article_by_id(db, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="기사를 찾을 수 없습니다.")

    # 사용자 프로필 존재 확인
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="사용자 프로필을 찾을 수 없습니다.")

    # LLM 분석 생성
    user_profile = {
        "region": user.region,
        "age": user.age,
        "gender": user.gender,
        "job": user.job,
        "interest": user.interest,
    }
    result = await generate_analysis(article.content, user_profile)

    return ArticleAnalysis(
        article_id=article_id,
        effect=result["effect"],
        solution=result["solution"],
    )


# ── GET /articles/{article_id} ────────────────────────────

@router.get("/{article_id}", response_model=ArticleDetail)
async def get_article(article_id: int, db: AsyncSession = Depends(get_db)):
    article = await get_article_by_id(db, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="기사를 찾을 수 없습니다.")

    common = await get_common_analysis(db, article_id)

    return ArticleDetail(
        article_id=article.article_id,
        title=article.title,
        date=article.date,
        content=article.content,
        category=article.category.value,
        source_url=article.source_url,
        summary=common.summary if common else None,
        terms=common.terms if common else None,
    )
