from datetime import datetime, timedelta
import app.crud.article as article_crud
import app.crud.user as user_crud
from app.services.llm.openai_client import get_embedding
from app.services.llm_service import generate_common_analysis


async def create_article_recommendation(db, user_id):
    # 1. 최근 1일 동안의 뉴스만 필터링하기
    now = datetime.now()
    recent_24_hours = now - timedelta(hours=24)

    articles = article_crud.get_articles_by_published_at(db, recent_24_hours)

    # 2. 필터링된 각 뉴스의 임베딩과 사용자 정보의 코사인 유사도 계산
    #   2-1. 뉴스에 임베딩/요약 정보가 없으면 생성하기
    for article in articles:
        if article["embedding"] is None:
            if article["summary"] is None:
                # 뉴스에 요약 정보가 없을 시 생성 요약+임베딩 한번에 생성
                result = generate_common_analysis(article)
                article_crud.update_article_by_id(
                    db, article["id"], result
                )  # DB에 저장
            else:
                # 뉴스에 임베딩 정보가 없을 시 임베딩만 생성
                article_embedding = get_embedding(article["summary"])
                article_crud.update_article_by_id(
                    db, article["id"], {"embedding": article_embedding}
                )  # DB에 저장

    # 3. 사용자 정보 불러오기
    #   3-1. 사용자 정보 임베딩이 없으면 생성하기
    user = user_crud.get_user_by_id(db, user_id)
    if user["embedding"] is None:
        user_embedding = get_embedding(user["extra_information"])
        user_crud.update_user(db, user_id, {"embedding": user_embedding})  # DB에 저장
    else:
        user_embedding = user["embedding"]

    # 4. 코사인 유사도가 높은 상위 10개 반환
    return article_crud.get_articles_by_cosine_similarity(
        db=db,
        date=recent_24_hours,
        user_embedding=user_embedding,
        limit=10,
    )
