from sqlalchemy.orm import Session

import app.crud.article as article_crud
import app.crud.personal_analysis as personal_crud
import app.crud.user as user_crud
from datetime import datetime, timedelta
import numpy as np

from app.models.article import Article
from app.models.user import User
from app.exceptions.domain import ArticleNotFoundError, UserNotFoundError
from app.services.llm_service import (
    generate_common_analysis,
    generate_personal_analysis,
    generate_article_embedding,
    generate_user_profile_embedding,
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


async def get_common_analysis(db: Session, article_id: int) -> Article:
    article = article_crud.get_article_by_id(db, article_id)

    if article is None:
        raise ArticleNotFoundError()

    # DB에 공통해설이 없으면 LLM API 호출
    if article.summary is None or article.keyword is None:
        common_analysis = await generate_common_analysis(article)

        article = article_crud.update_article_by_id(
            db,
            article_id,
            common_analysis,
        )

    return article


async def get_personal_analysis(db: Session, article_id: int, user_id: int) -> dict:
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

    # if user.behavior_embedding and article.embedding:
    #     updated_behavior = [
    #         (b_val * 0.9) + (a_val * 0.1)
    #         for b_val, a_val in zip(user.behavior_embedding, article.embedding)
    #     ]
    #     user_crud.update_user(db, user.id, {"behavior_embedding": updated_behavior})

    ### 사용자가 클릭한 기사 정보를 반영하여 행동 임베딩 업데이트

    # 사용자의 행동 임베딩 불러오기, 없을 시 프로필 임베딩으로 설정
    if user.behavior_embedding is None:
        # 프로필 임베딩이 없을 시 새로 생성
        if user.profile_embedding is None:
            profile_embedding = await generate_user_profile_embedding(user)
            user_crud.update_user(db, user_id, {"profile_embedding": profile_embedding})
            behavior_embedding = profile_embedding
        else:
            behavior_embedding = user.profile_embedding
    else:
        behavior_embedding = user.behavior_embedding

    # 기사 임베딩 불러오기, 없을 시 생성
    if article.embedding is None:
        article_embedding = await generate_article_embedding(article)
        article_crud.update_article_by_id(
            db, article_id, {"embedding": article_embedding}
        )
    else:
        article_embedding = article.embedding

    # 기존 임베딩 : 새로 추가될 기사 임베딩의 반영 비율을 0.9: 0.1로 정하고 가중합
    behavior_embedding = behavior_embedding * 0.9 + article_embedding * 0.1
    behavior_embedding /= np.linalg.norm(behavior_embedding)  # 정규화
    user_crud.update_user(db, user_id, {"behavior_embedding": behavior_embedding})

    return personal_analysis
