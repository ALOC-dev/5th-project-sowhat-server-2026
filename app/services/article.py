import app.crud.article as article_crud
import app.crud.personal_analysis as personal_crud
import app.crud.user as user_crud
from datetime import datetime

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

def get_recommended_articles(db, user_id):
    
    # 1차 명시적 프로필(관심사/직업/지역) 가중치 + 2차 행동형(누적 태그 점수) 가중치 + 최신성 종합 점수를 계산하여 상위 20개 기사를 반환한다    
    
    user = user_crud.get_user_by_id(db, user_id)
    if user is None:
        raise UserNotFoundError()
        
    # 2차 행동형 : user_crud에서 JSON 취향 점수판 가져오기
    user_interests = user_crud.get_user_interest_scores(db, user_id) or {}
    
    all_articles = article_crud.get_all_articles(db)
    scored_articles = []
    current_time = datetime.now()
    
    for article in all_articles:
        score = 0.0
        
        # [2차 행동형 가중치] 누적된 태그 점수와 기사 키워드 매칭
        if article.keyword:
            article_keywords = [k.strip() for k in article.keyword.split(",")] if isinstance(article.keyword, str) else article.keyword
            for keyword in article_keywords:
                score += user_interests.get(keyword, 0) * 2.0  # 읽은 횟수당 2점씩 가중치
                
        # [1차 프로필 가중치] 가입 시 설정한 기본 관심 카테고리 일치 여부
        if user.interest and getattr(article, "category", None) == user.interest:
            score += 15.0  # 기본 타겟 관심사 가중치 크게 부여
                
        # [1차 프로필 가중치] 인적 사항 일치 여부 (직업, 지역 등)
        if getattr(article, "target_job", None) == user.job:
            score += 5.0
        if getattr(article, "target_region", None) == user.region:
            score += 3.0

        # D. [기본 가중치] 최신성 가중치 (등록된 지 얼마 안 된 기사들)
        if getattr(article, "created_at", None):
            time_delta = (current_time - article.created_at).total_seconds() / 3600  # 시간 기준 차이
            if time_delta <= 24:
                score += 10.0  # 24시간 이내 최신 기사
            elif time_delta <= 72:
                score += 5.0
            
        scored_articles.append((score, article))
        
    scored_articles.sort(key=lambda x: x[0], reverse=True)
    top_20_articles = [item[1] for item in scored_articles[:20]]
    
    for article in top_20_articles:
        if len(article.content) > 25:
            article.content = article.content[:25] + "..."
            
    return top_20_articles