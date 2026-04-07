import app.crud.article as article_crud
import app.crud.common_analysis as common_crud
import app.crud.personal_analysis as personal_crud
import app.crud.user as user_crud

from app.exceptions import (
    ArticleNotFoundError,
    AnalysisNotFoundError,
    UserNotFoundError,
)

# from app.core.llm import generate_analysis


def get_all_articles(db):
    articles = article_crud.get_all_articles()

    for a in articles:
        if len(a["content"]) > 25:
            a["content"] = a["content"][:25] + "..."  # 기사 내용 25자까지만 자르기

    return articles


def get_common_analysis(db, article_id):
    article = article_crud.get_article_by_id(article_id)
    if not article:
        return ArticleNotFoundError

    common = common_crud.get_analysis_by_article(article_id)
    if not common:
        # DB에 저장된 것이 없을 경우 LLaMA API 호출 -> 요약/용어설명 생성, DB에 저장
        return AnalysisNotFoundError  # 임시 코드

    article.update(common)  # 기사 상세정보에 공통요약 정보 추가
    return article


def get_personal_analysis(db, article_id, user_id):
    article = article_crud.get_article_by_id(article_id)
    if not article:
        raise ArticleNotFoundError

    user = user_crud.get_user_by_id(user_id)
    if not user:
        raise UserNotFoundError

    personal = personal_crud.get_analysis_by_article_and_user(article_id, user_id)
    if not personal:
        # DB에 저장된 것이 없을 경우 GPT/Groq API 호출 -> 개인 맞춤 솔루션 생성, DB에 저장
        return AnalysisNotFoundError  # 임시 코드

    return personal
