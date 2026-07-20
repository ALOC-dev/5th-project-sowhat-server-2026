from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

import app.crud.article as article_crud
import app.crud.personal_analysis as personal_crud
import app.crud.user as user_crud

from app.models.article import Article
from app.exceptions.domain import ArticleNotFoundError, UserNotFoundError
from app.services.embedding_tasks import (
    ensure_article_embedding,
    update_behavior_embedding,
)
from app.services.llm_service import (
    generate_common_analysis,
    generate_personal_analysis,
)
from app.services.recommend import recommend_by_cosine_similarity


def get_all_articles(db: Session) -> list[Article]:
    articles = article_crud.get_all_articles(db)

    for article in articles:
        if len(article.content) > 25:
            article.content = article.content[:25] + "..."

    return articles


async def get_recommended_articles(db: Session, user_id: int) -> list[Article]:
    user = user_crud.get_user_by_id(db, user_id)
    if user is None:
        raise UserNotFoundError()

    # top_20_articles = await recommend_service.recommend_by_weights(db, user) # recommend.py로 이관한 가중치 추천 로직 호출
    top_20_articles = await recommend_by_cosine_similarity(db, user)

    for article in top_20_articles:
        if len(article.content) > 25:
            article.content = article.content[:25] + "..."

    return top_20_articles


async def get_common_analysis(
    db: Session, article_id: int, background_tasks: BackgroundTasks
) -> Article:
    article = article_crud.get_article_by_id(db, article_id)

    if article is None:
        raise ArticleNotFoundError()

    # DB에 공통해설이 없으면 LLM API 호출
    if article.summary is None or article.keyword is None:
        common_analysis = await generate_common_analysis(article)

        article = article_crud.update_article_by_id(
            db,
            article_id,
            {
                "summary": common_analysis["summary"],
                "keyword": common_analysis["keyword"],
            },
        )

    # 기사 임베딩은 당장 필요하지 않으므로 응답 후 백그라운드에서 생성
    if article.embedding is None:
        background_tasks.add_task(ensure_article_embedding, article_id)

    return article


async def get_personal_analysis(
    db: Session, article_id: int, user_id: int, background_tasks: BackgroundTasks
) -> dict:
    article = article_crud.get_article_by_id(db, article_id)

    if article is None:
        raise ArticleNotFoundError()

    user = user_crud.get_user_by_id(db, user_id)

    if user is None:
        raise UserNotFoundError()

    # DB에 개인해설이 존재하는지 확인
    personal = personal_crud.get_analysis_by_article_and_user(
        db,
        article_id,
        user_id,
    )

    if personal:
        return personal

    personal_analysis = await generate_personal_analysis(article, user)

    personal_crud.create_analysis(
        db,
        {
            "article_id": article_id,
            "user_id": user_id,
            **personal_analysis,
        },
    )

    # 행동 임베딩 업데이트(필요 시 프로필/기사 임베딩 생성 포함)는
    # 당장 필요하지 않으므로 응답 후 백그라운드에서 처리
    background_tasks.add_task(update_behavior_embedding, user_id, article_id)

    return personal_analysis
