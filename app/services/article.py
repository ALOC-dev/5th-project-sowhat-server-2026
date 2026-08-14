from datetime import datetime

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

import app.crud.article as article_crud
import app.crud.personal_analysis as personal_crud
import app.crud.experience_analysis as experience_analysis_crud

from app.db.database import SessionLocal
from app.models.article import Article
from app.models.personal_analysis import PersonalAnalysis
from app.exceptions.domain import ArticleNotFoundError, UserNotFoundError
from app.models.enums import AgeGroupEnum, CategoryEnum, JobEnum
from app.models.user import User
from app.services.llm.embedding_tasks import (
    ensure_article_embedding,
    update_behavior_embedding,
)
from app.services.llm_service import (
    generate_common_analysis,
    generate_personal_analysis,
    generate_experience_analysis,
    select_search_result,
)
from app.services.llm.recommend import recommend_by_cosine_similarity

PREVIEW_CONTENT_LENGTH = 25
RECOMMENDATION_TOP_K = 5


# 목록 응답에는 본문 전체가 필요 없어 미리보기 길이로 잘라 내보낸다
def _truncate_preview_content(articles: list[Article]) -> list[Article]:
    for article in articles:
        if len(article.content) > PREVIEW_CONTENT_LENGTH:
            article.content = article.content[:PREVIEW_CONTENT_LENGTH] + "..."

    return articles


def get_all_articles(
    db: Session,
    category: CategoryEnum | None,
    limit: int,
    offset: int,
) -> list[Article]:
    articles = article_crud.get_all_articles(db, category, limit, offset)

    return _truncate_preview_content(articles)


async def get_recommended_articles(db: Session, user: User) -> list[Article]:

    top_k_articles = await recommend_by_cosine_similarity(
        db, user, RECOMMENDATION_TOP_K
    )

    return _truncate_preview_content(top_k_articles)


# 사용자가 조회한 기사 목록 (최근 조회 순)
# 조회 기록은 개인해설이 생성될 때 personal_analysis에 남고,
# 목록에 필요한 기사 정보(title, category)도 그때 함께 저장된다
def get_viewed_articles(
    db: Session, user_id: int, limit: int, offset: int
) -> list[PersonalAnalysis]:
    return personal_crud.get_viewed_analyses(db, user_id, limit, offset)


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

    # 기사 임베딩이 없을 경우 백그라운드에서 생성
    if article.embedding is None:
        background_tasks.add_task(ensure_article_embedding, article_id)

    article.content = article.content[:120] + "..."
    return article


# 비로그인 사용자용 개인해설 미리보기 (effect만 생성, 임베딩 처리 없음)
# (article_id, age_group, job, interest) 조합으로 캐시해 재활용하고, 없을 때만 LLM 호출
async def get_experience_analysis(
    db: Session,
    article_id: int,
    age_group: AgeGroupEnum,
    job: JobEnum,
    interest: CategoryEnum,
) -> dict:
    cached = experience_analysis_crud.get_experience_analysis(
        db, article_id, age_group, job, interest
    )
    if cached:
        return {"effect": cached.effect}

    article = article_crud.get_article_by_id(db, article_id)
    if article is None:
        raise ArticleNotFoundError()

    experience_analysis = await generate_experience_analysis(
        article, age_group.value, job.value, interest.value
    )

    experience_analysis_crud.create_experience_analysis(
        db,
        {
            "article_id": article_id,
            "age_group": age_group,
            "job": job,
            "interest": interest,
            "effect": experience_analysis["effect"],
        },
    )

    return experience_analysis


# SSE: 해설과 검색에 쓰일 링크 이름만 반환하는 함수
async def sse_get_personal_analysis(
    db, user: User, article_id: int, background_tasks: BackgroundTasks
) -> tuple[dict, list]:
    article = article_crud.get_article_by_id(db, article_id)
    if article is None:
        raise ArticleNotFoundError()

    # DB에 개인해설이 존재하는지 확인
    personal_analysis = personal_crud.get_analysis_by_article_and_user(
        db,
        article_id,
        user.id,
    )
    if personal_analysis:
        return (
            {
                "effect": personal_analysis.effect,
                "solution": personal_analysis.solution,
                "links": personal_analysis.links,
                "similar_articles": personal_analysis.similar_articles,
            },
            [],
        )  # 링크 추가 검색이 필요 없으므로 link_names 자리는 비우기

    # 과거 유사 기사를 함께 넘겨 개인해설이 지어낸 사례 대신 실제 보도를 근거로 삼게 한다
    related_articles = article_crud.find_related_past_articles(db, article)

    time_start = datetime.now()
    personal_analysis = await generate_personal_analysis(
        article,
        user,
        related_articles,
    )
    time_elapsed = datetime.now() - time_start
    print("[개인 해설 생성]", time_elapsed)

    link_targets = personal_analysis.pop("link_targets", [])

    similar_articles = []
    for ra in related_articles:
        similar_articles.append(
            {
                "title": ra.title,
                "published_at": f"{ra.published_at:%Y.%m.%d}",
                "publisher": ra.publisher,
                "source_url": ra.source_url,
            }
        )
    personal_analysis["similar_articles"] = similar_articles

    created = personal_crud.create_analysis(
        db,
        {
            "article_id": article_id,
            "user_id": user.id,
            "title": article.title,
            "category": article.category,
            **personal_analysis,
        },
    )

    # 링크 검색 결과 업데이트를 위해 id 추가
    personal_analysis["id"] = created.id

    # 행동 임베딩 업데이트(필요 시 프로필/기사 임베딩 생성 포함)는
    # 당장 필요하지 않으므로 응답 후 백그라운드에서 처리
    background_tasks.add_task(update_behavior_embedding, user, article)

    return personal_analysis, link_targets


async def sse_update_search_result(
    personal_analysis: dict, link_targets: list[str]
) -> list[dict]:
    # SSE 요청이 끊어졌을 때 db 세션이 함께 닫힐 위험이 있어 함수 내에서 따로 열기
    db = SessionLocal()

    try:
        selected_links = await select_search_result(
            personal_analysis["solution"], link_targets
        )

        personal_crud.update_analysis(
            db,
            personal_analysis["id"],
            {"links": selected_links},
        )

        return selected_links

    finally:
        db.close()
