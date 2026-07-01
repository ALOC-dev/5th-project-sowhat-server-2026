from datetime import datetime, timedelta
import app.crud.article as article_crud
import app.crud.user as user_crud
from app.services.llm.openai_client import get_embedding
from app.services.llm_service import generate_common_analysis 

async def recommend_by_cosine_similarity(db, user):

    # 1. 최근 1일 동안의 뉴스만 필터링하기
    now = datetime.now()
    recent_24_hours = now - timedelta(hours=24)

    articles = article_crud.get_articles_by_date(db, recent_24_hours)

    # 2. 필터링된 각 뉴스의 임베딩과 사용자 정보의 코사인 유사도 계산
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

    # 3. 사용자 정보 불러오기 및 고품질 초기 임베딩 생성
    if user.embedding is None:
        profile_text = (
            f"나이: {user.age}, 성별: {user.gender}, 직업: {user.job}, "
            f"관심사: {user.interest}, 목적: {user.purpose}, 추가정보: {user.extra_information}"
        )
        user_embedding = await get_embedding(profile_text)
        user_crud.update_user(db, user.id, {"embedding": user_embedding})  # DB에 저장
    else:
        user_embedding = user.embedding

    # 4. 코사인 유사도가 높은 상위 10개 반환
    return article_crud.get_articles_by_cosine_similarity(
        db=db,
        date=recent_24_hours,
        user_embedding=user_embedding,
        limit=10,
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
