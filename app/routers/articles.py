from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request
from fastapi.sse import EventSourceResponse, ServerSentEvent
from sqlalchemy.orm import Session
from app.db.database import get_db

from app.schemas.article import ArticlePreviewResponse, ArticleDetailResponse
from app.schemas.personal_analysis import PersonalAnalysis

import app.services.article as article_service
import app.services.auth as auth_service

router = APIRouter(prefix="/api/articles", tags=["articles"])


# ── GET /articles ─────────────────────────────────────────
@router.get("", response_model=list[ArticlePreviewResponse])
def list_articles(
    db: Session = Depends(get_db),
):
    return article_service.get_all_articles(db)


# ── GET /articles/recommendations ─────────────────────────
@router.get("/recommendations", response_model=list[ArticlePreviewResponse])
async def get_recommended_articles(
    request: Request,
    db: Session = Depends(get_db),
):
    current_user = auth_service.get_current_user(db, request)

    recommendation = await article_service.get_recommended_articles(db, current_user)
    return recommendation


# ── GET /articles/{article_id} ────────────────────────────
@router.get("/{article_id}", response_model=ArticleDetailResponse)
async def get_article(
    article_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    article_detail = await article_service.get_common_analysis(
        db, article_id, background_tasks
    )
    return article_detail


# ── GET /articles/{article_id}/analysis/stream ─────────────
@router.get("/{article_id}/analysis/stream", response_class=EventSourceResponse)
async def get_personal_analysis_stream(
    background_tasks: BackgroundTasks,
    article_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    try:
        current_user = auth_service.get_current_user(db, request)

        analysis, link_targets = await article_service.sse_get_personal_analysis(
            db, current_user, article_id, background_tasks
        )

        yield ServerSentEvent(data=analysis, event="analysis")

        if len(link_targets) > 0:
            yield ServerSentEvent(
                data=await article_service.sse_update_search_result(
                    db, analysis, link_targets
                ),
                event="links",
            )

    except Exception as exc:
        print(exc)
        yield ServerSentEvent(data=exc, event="error")

    finally:
        yield ServerSentEvent(data={}, event="done")
