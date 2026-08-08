from datetime import datetime

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

import app.crud.article as article_crud
import app.crud.personal_analysis as personal_crud
import app.crud.user as user_crud

from app.models.article import Article
from app.models.personal_analysis import PersonalAnalysis
from app.exceptions.domain import ArticleNotFoundError, UserNotFoundError
from app.services.llm.embedding_tasks import (
    ensure_article_embedding,
    update_behavior_embedding,
)
from app.services.llm_service import (
    generate_common_analysis,
    generate_personal_analysis,
    select_search_result,
)
from app.services.llm.recommend import recommend_by_cosine_similarity


PREVIEW_CONTENT_LENGTH = 25


# 목록 응답에는 본문 전체가 필요 없어 미리보기 길이로 잘라 내보낸다
def _truncate_preview_content(articles: list[Article]) -> list[Article]:
    for article in articles:
        if len(article.content) > PREVIEW_CONTENT_LENGTH:
            article.content = article.content[:PREVIEW_CONTENT_LENGTH] + "..."

    return articles


def get_all_articles(db: Session) -> list[Article]:
    articles = article_crud.get_all_articles(db)

    return _truncate_preview_content(articles)


async def get_recommended_articles(db: Session, user_id: int) -> list[Article]:
    user = user_crud.get_user_by_id(db, user_id)
    if user is None:
        raise UserNotFoundError()

    top_20_articles = await recommend_by_cosine_similarity(db, user)

    return _truncate_preview_content(top_20_articles)


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

    # 여기서 select_search_result를 백그라운드로 빼고싶다...
    # 아님 프론트에서 선 해설 요청 -> 후 링크 요청으로 따로 만들어..?

    # 화이트리스트에 없는 창구 이름은 Tavily 검색 후 2차 LLM이 선택한 실제 검색 결과를 links에 추가
    # search_link_targets = personal_analysis.pop("link_targets", [])

    selected_links = await select_search_result(
        personal_analysis["solution"], personal_analysis.pop("link_targets", [])
    )

    personal_analysis["links"] = selected_links

    personal_crud.create_analysis(
        db,
        {
            "article_id": article_id,
            "user_id": user_id,
            "title": article.title,
            "category": article.category,
            **personal_analysis,
        },
    )

    # 행동 임베딩 업데이트(필요 시 프로필/기사 임베딩 생성 포함)는
    # 당장 필요하지 않으므로 응답 후 백그라운드에서 처리
    background_tasks.add_task(update_behavior_embedding, user_id, article_id)

    return personal_analysis
