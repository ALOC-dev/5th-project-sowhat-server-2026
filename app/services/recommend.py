from datetime import datetime, timedelta
import numpy as np

import app.crud.article as article_crud
import app.crud.user as user_crud
from app.services.llm.openai_client import get_embedding
from app.services.llm_service import (
    generate_common_analysis,
    generate_user_profile_embedding,
)


# 사용자 프로필의 세부항목별로 가중치를 조절해 프로필 임베딩을 구하는 계산 함수
def calculate_profile_embedding(embeddings):
    """
    각 임베딩을 다음 비율로 가중합하고 정규화해 사용자 프로필 임베딩을 구한다.
    (0) 나이/성별 0.1
    (1) 직업/지역 0.2
    (2) 관심사 0.3
    (3) 목적 0.2
    (4) 추가 정보 0.2
    """
    profile_embedding = (
        embeddings[0] * 0.1
        + embeddings[1] * 0.2
        + embeddings[2] * 0.3
        + embeddings[3] * 0.2
        + embeddings[4] * 0.2
    )
    profile_embedding /= np.linalg.norm(profile_embedding)  # 정규화

    return profile_embedding


# 기사 클릭 시 사용자의 행동 임베딩에 반영하기 위한 계산 함수
def calculate_behavior_embedding(original_embedding, new_embedding):
    # 기존 임베딩 : 새로 추가될 임베딩의 반영 비율을 0.95: 0.05로 정하고 가중합
    behavior_embedding = original_embedding * 0.95 + new_embedding * 0.05
    behavior_embedding /= np.linalg.norm(behavior_embedding)  # 정규화
    return behavior_embedding


# 사용자의 프로필 임베딩, 행동 임베딩을 최종적으로 합치는 함수
def calculate_final_user_embedding(p_embedding, b_embedding):
    # 두 임베딩을 0.7 : 0.3 비율로 가중합
    final_user_embedding = p_embedding * 0.7 + b_embedding * 0.3
    final_user_embedding /= np.linalg.norm(final_user_embedding)  # 정규화
    return final_user_embedding


async def recommend_by_cosine_similarity(db, user):
    # 1. 최근 1일 동안의 뉴스만 필터링하기
    now = datetime.now()
    recent_24_hours = now - timedelta(hours=24)

    articles = article_crud.get_articles_by_date(db, recent_24_hours)

    # 2. 필터링된 각 뉴스의 임베딩 불러오기
    #   2-1. 뉴스에 임베딩/요약 정보가 없으면 생성하기
    for article in articles:
        if article.embedding is None:
            if article.summary is None:
                # 뉴스에 요약 정보가 없을 시 생성 요약+임베딩 한번에 생성
                result = await generate_common_analysis(article)
                article_crud.update_article_by_id(db, article.id, result)  # DB에 저장
            else:
                # 뉴스에 임베딩 정보가 없을 시 임베딩만 생성
                article_embedding = await get_embedding(article.summary)
                article_crud.update_article_by_id(
                    db, article.id, {"embedding": article_embedding}
                )  # DB에 저장

    # 3. 사용자의 프로필 임베딩 불러오기
    #   3-1. 프로필 임베딩이 없을 경우 생성
    if user.profile_embedding is None:
        # 사용자 정보의 각 항목 임베딩을 리스트로 받아오기
        embeddings = await generate_user_profile_embedding(user)
        # 배정된 가중치에 따라 프로필 임베딩 계산
        p_embedding = calculate_profile_embedding(embeddings)

        user_crud.update_user(
            db, user.id, {"profile_embedding": p_embedding}
        )  # DB에 저장
    else:
        p_embedding = user.profile_embedding

    # 4. 사용자의 행동 임베딩 불러오기
    #   4-1. 없을 경우 프로필 임베딩으로 초기화
    if user.behavior_embedding is None:
        b_embedding = p_embedding.copy()
        user_crud.update_user(
            db, user.id, {"behavior_embedding": b_embedding}
        )  # DB에 저장
    else:
        b_embedding = user.behavior_embedding

    # 5. 프로필, 행동 임베딩을 하나로 합침
    final_user_embedding = calculate_final_user_embedding(p_embedding, b_embedding)

    # 6. 결합된 하이브리드 벡터로 코사인 유사도가 높은 상위 20개 반환
    return article_crud.get_articles_by_cosine_similarity(
        db=db,
        date=recent_24_hours,
        user_embedding=final_user_embedding,
        limit=20,
    )


def recommend_by_weights(db, user):
    """프로필 가중치 + 최신성 종합 점수 계산"""
    user_interests = user_crud.get_user_interest_scores(db, user.id) or {}
    all_articles = article_crud.get_all_articles(db)
    scored_articles = []
    current_time = datetime.now()

    for article in all_articles:
        score = 0.0

        # 2차 행동형 가중치: 키워드 매칭
        if article.keyword:
            article_keywords = (
                [k.strip() for k in article.keyword.split(",")]
                if isinstance(article.keyword, str)
                else article.keyword
            )
            for keyword in article_keywords:
                score += user_interests.get(keyword, 0) * 2.0

        # 1차 프로필 가중치: 관심 카테고리 일치
        if user.interest and getattr(article, "category", None) == user.interest:
            score += 15.0

        # 1차 프로필 가중치: 직업, 지역 일치
        if getattr(article, "target_job", None) == user.job:
            score += 5.0
        if getattr(article, "target_region", None) == user.region:
            score += 3.0

        # 최신성 가중치
        if getattr(article, "created_at", None):
            time_delta = (current_time - article.created_at).total_seconds() / 3600
            if time_delta <= 24:
                score += 10.0
            elif time_delta <= 72:
                score += 5.0

        scored_articles.append((score, article))

    scored_articles.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in scored_articles[:20]]
