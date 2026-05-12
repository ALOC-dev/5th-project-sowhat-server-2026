from copy import deepcopy

import app.crud.article as article_crud
import app.crud.common_analysis as common_crud
import app.crud.personal_analysis as personal_crud
import app.crud.user as user_crud

from app.exceptions import (
    ArticleNotFoundError,
    UserNotFoundError,
)

from app.services.llm_service import (
    generate_common_analysis_with_groq,
    generate_personal_analysis_with_groq,
)

# from app.core.llm import generate_analysis

def get_all_articles(db):
    articles = deepcopy(article_crud.get_all_articles())

    for a in articles:
        if len(a["content"]) > 25:
            a["content"] = a["content"][:25] + "..."  # 기사 내용 25자까지만 자르기

    return articles


async def get_common_analysis(db, article_id):
    article = article_crud.get_article_by_id(article_id)
    if not article:
        raise ArticleNotFoundError

    common = common_crud.get_analysis_by_article(article_id)

    if not common:
        result = await generate_common_analysis_with_groq(
            title=article["title"],
            content=article["content"],
            category=article["category"],
        )

        article_detail = deepcopy(article)
        article_detail["summary"] = result["summary"]
        article_detail["keyword"] = result["keyword"]
        return article_detail


    article_detail = deepcopy(article)
    article_detail.update(common) # 기사 상세정보에 공통요약 정보 추가
    return article_detail


async def get_personal_analysis(db, article_id, user_id):
    article = article_crud.get_article_by_id(article_id)
    if not article:
        raise ArticleNotFoundError

    user = user_crud.get_user_by_id(db, user_id)
    if not user:
        raise UserNotFoundError

    personal = personal_crud.get_analysis_by_article_and_user(article_id, user_id)

    if not personal:
        if isinstance(user, dict):
            user_profile = {
                "age": user["age"],
                "gender": user["gender"],
                "region": user["region"],
                "job": user["job"],
                "interest": user["interest"],
            }
        else:
            user_profile = {
                "age": user.age,
                "gender": user.gender,
                "region": user.region,
                "job": user.job,
                "interest": user.interest,
            }

        result = await generate_personal_analysis_with_groq(
            title=article["title"],
            content=article["content"],
            category=article["category"],
            user_profile=user_profile,
        )

        return result

    return personal
