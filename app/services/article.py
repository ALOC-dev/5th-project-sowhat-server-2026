import app.crud.article as article_crud
import app.crud.personal_analysis as personal_crud
import app.crud.user as user_crud
from datetime import datetime, timedelta

from app.exceptions.domain import ArticleNotFoundError, UserNotFoundError
from app.services.llm_service import generate_common_analysis, generate_personal_analysis
import app.services.recommend as recommend_service


def get_all_articles(db):
    articles = article_crud.get_all_articles(db)

    for article in articles:
        if len(article.content) > 25:
            article.content = article.content[:25] + "..."

    return articles

    # 2차 행동형 : user_crud에서 JSON 취향 점수판 가져오기
    user_interests = user_crud.get_user_interest_scores(db, user_id) or {}

    all_articles = article_crud.get_all_articles(db)
    
def get_recommended_articles(db, user_id):
    user = user_crud.get_user_by_id(db, user_id)
    if user is None:
        raise UserNotFoundError()

    # recommend.py로 이관한 가중치 추천 로직 호출
    top_20_articles = recommend_service.recommend_by_weights(db, user)

    for article in top_20_articles:
        if len(article.content) > 25:
            article.content = article.content[:25] + "..."

    return top_20_articles

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

    if user.embedding and article.embedding:
        updated_embedding = [
            (u_val * 0.9) + (a_val * 0.1) 
            for u_val, a_val in zip(user.embedding, article.embedding)
        ]
        user_crud.update_user(db, user.id, {"embedding": updated_embedding})

    return result
