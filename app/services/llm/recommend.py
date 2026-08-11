from datetime import datetime, timedelta
import numpy as np
from sqlalchemy.orm import Session

import app.crud.article as article_crud
from app.models.article import Article
from app.models.user import User
from app.services.llm.embedding_tasks import (
    ensure_article_embedding,
    get_or_create_user_embedding,
)


async def recommend_by_cosine_similarity(
    db: Session, user: User, top_k: int = 20
) -> list[Article]:
    # 1. 최근 1일 동안의 뉴스만 필터링하기
    now = datetime.now()
    recent_24_hours = now - timedelta(hours=24)

    articles = article_crud.get_articles_by_date(db, recent_24_hours)

    # 2. 필터링된 각 뉴스에 임베딩/요약 정보가 없을 경우 생성하기
    for article in articles:
        await ensure_article_embedding(article.id)

    # 3. 사용자의 프로필 및 행동 임베딩 불러오기
    #   3-1. 프로필/행동 임베딩이 없을 경우 생성
    p_embedding, b_embedding = get_or_create_user_embedding(db, user)

    # 4. 사용자 프로필 임베딩, 행동 임베딩을 하나로 합침
    #   4-1. 두 임베딩을 0.7 : 0.3 비율로 가중합
    #   4-2. 벡터 크기를 1로 유지하기 위해 정규화
    final_user_embedding = p_embedding * 0.7 + b_embedding * 0.3
    final_user_embedding /= np.linalg.norm(final_user_embedding)

    # 5. 결합된 하이브리드 벡터로 코사인 유사도가 높은 상위 20개 반환
    return article_crud.find_similar_articles(
        db=db,
        date=recent_24_hours,
        user_embedding=final_user_embedding,
        limit=top_k,
    )
