import app.crud.article as article_crud
import app.crud.personal_analysis as personal_crud
import app.crud.user as user_crud

from app.exceptions.domain import (
    ArticleNotFoundError,
    UserNotFoundError,
)

from app.services.llm_service import (
    generate_common_analysis,
    generate_personal_analysis,
)


def get_all_articles(db):
    articles = article_crud.get_all_articles(db)

    for article in articles:
        if len(article.content) > 25:
            article.content = article.content[:25] + "..."

    return articles


async def get_common_analysis(db, article_id):
    article = article_crud.get_article_by_id(db, article_id)

    if article is None:
        raise ArticleNotFoundError()

    # DB에 공통해설이 없으면 LLM API 호출
    if article.summary is None or article.keyword is None:
        article_data = {
            "title": article.title,
            "content": article.content,
            "category": article.category,
        }

        result = await generate_common_analysis(article_data)

        article_crud.update_article_by_id(
            db,
            article_id,
            result,
        )

        # 최신 상태 다시 조회
        article = article_crud.get_article_by_id(db, article_id)

    return article


async def get_personal_analysis(db, article_id, user_id):
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

    article_data = {
        "title": article.title,
        "content": article.content,
        "category": article.category,
    }

    user_profile = {
        "age": user.age,
        "gender": user.gender,
        "region": user.region,
        "job": user.job,
        "interest": user.interest,
        "purpose": user.purpose,
    }

    result = await generate_personal_analysis(
        article_data,
        user_profile,
    )

    personal_crud.create_analysis(
        db,
        {
            "article_id": article_id,
            "user_id": user_id,
            **result,
        },
    )

    return result