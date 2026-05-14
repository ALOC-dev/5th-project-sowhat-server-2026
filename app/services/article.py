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

    article_detail = deepcopy(article)  # 기사 상세정보 복사 (공통해설 추가하기 위함)

    # DB에 공통해설이 존재하는지 확인
    common = common_crud.get_analysis_by_article(article_id)
    if common:
        article_detail.update(common)  # 기사 상세정보에 공통 해설 추가

    # 없으면 LLM API호출로 해설 생성하기
    if isinstance(article, dict):
        article_data = {
            "title": article["title"],
            "content": article["content"],
            "category": article["category"] or "미분류",
        }
    else:
        article_data = {
            "title": article.title,
            "content": article.content,
            "category": article.category or "미분류",
        }

    result = await generate_common_analysis_with_groq(article_data)
    common_crud.create_analysis(result)  # 생성된 공통 해설을 DB에 저장

    article_detail.update(result)  # 기사 상세정보에 공통 해설 추가
    return article_detail


async def get_personal_analysis(db, article_id, user_id):
    article = article_crud.get_article_by_id(article_id)
    if not article:
        raise ArticleNotFoundError

    user = user_crud.get_user_by_id(db, user_id)
    if not user:
        raise UserNotFoundError

    # DB에 개인해설이 존재하는지 확인
    personal = personal_crud.get_analysis_by_article_and_user(article_id, user_id)
    if personal:
        return personal

    # 없으면 LLM API호출로 해설 생성하기
    if isinstance(article, dict):
        article_data = {
            "title": article["title"],
            "content": article["content"],
            "category": article["category"] or "미분류",
        }
    else:
        article_data = {
            "title": article.title,
            "content": article.content,
            "category": article.category or "미분류",
        }

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

    result = await generate_personal_analysis_with_groq(article_data, user_profile)
    result.update({"article_id": article_id, "user_id": user_id})
    personal_crud.create_analysis(result)  # 생성된 개인 해설을 DB에 저장

    return result
