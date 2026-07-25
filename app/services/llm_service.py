# import json
import numpy as np

# from app.services.llm.groq_client import create_json_completion
from app.models.article import Article
from app.models.user import User
from app.schemas.filtered_extra_information import FilteredExtraInformation
from app.services.llm.openai_client import create_json_completion, get_embedding
from app.services.llm.prompts import (
    COMMON_ANALYSIS_PROMPT,
    PERSONAL_ANALYSIS_PROMPT,
    SYSTEM_JSON_PROMPT,
    FILTER_EXTRA_INFORMATION_PROMPT,
)

from app.schemas.common_analysis import CommonAnalysis
from app.schemas.personal_analysis import PersonalAnalysis


async def generate_common_analysis(article: Article | dict) -> dict:
    # SQLAlchemy 모델에는 model_dump()가 없으므로 필요한 필드만 꺼내 dict로 변환
    if type(article) is Article:
        article = {
            "title": article.title,
            "category": article.category,
            "content": article.content,
        }

    prompt = COMMON_ANALYSIS_PROMPT.format(
        title=article["title"],
        category=article["category"].value,
        content=article["content"],
    )

    ### OpenAI
    response = await create_json_completion(
        messages=[
            {"role": "system", "content": SYSTEM_JSON_PROMPT},
            {"role": "user", "content": prompt},
        ],
        response_format=CommonAnalysis,
    )

    parsed = response.choices[0].message.parsed.model_dump()

    """
    returns: dict
        {
            "summary": str,
            "keyword": dict[str, str],
        }
    """
    return parsed


async def generate_personal_analysis(article: Article, user: User) -> dict:
    prompt = PERSONAL_ANALYSIS_PROMPT.format(
        title=article.title,
        category=article.category.value,
        content=article.content,
        age=user.age,
        gender=user.gender.value,
        region=user.region.value,
        job=user.job.value,
        interest=user.interest.value,
        purpose=user.purpose.value,
        extra_information=user.filtered_extra_information,
    )

    ### OpenAI
    response = await create_json_completion(
        messages=[
            {"role": "system", "content": SYSTEM_JSON_PROMPT},
            {"role": "user", "content": prompt},
        ],
        response_format=PersonalAnalysis,
    )

    parsed = response.choices[0].message.parsed.model_dump()

    """
    returns: dict
        {
            "effect": str,
            "solution": str,
        }
    """
    return parsed


# 채팅으로 사용자 추가정보 필터링을 요청하는 함수
async def filter_user_extra_information(
    extra_information: str,
) -> FilteredExtraInformation:
    normalized_information = extra_information.strip()

    if not normalized_information:
        return FilteredExtraInformation(
            success=True,
            summary="",
        )

    response = await create_json_completion(
        messages=[
            {
                "role": "developer",
                "content": FILTER_EXTRA_INFORMATION_PROMPT,
            },
            {
                "role": "user",
                "content": normalized_information,
            },
        ],
        response_format=FilteredExtraInformation,
    )

    return response.choices[0].message.parsed


# 기사 임베딩 생성 함수
# LLM으로 생성된 기사 요약본을 통해 임베딩 생성 (+필요시 해설 생성)
async def generate_article_embedding(article: Article | dict):
    # SQLAlchemy 모델에는 model_dump()가 없으므로 필요한 필드만 꺼내 dict로 변환
    if type(article) is Article:
        article = {
            "title": article.title,
            "category": article.category,
            "content": article.content,
            "summary": article.summary,
        }

    # 기사 요약 불러오기, 없을 시 생성해서 함께 반환
    if article["summary"] is None:
        common_analysis = await generate_common_analysis(article)
        summary = common_analysis["summary"]
        is_analysis_created = True
    else:
        summary = article["summary"]
        is_analysis_created = False

    embeddings = await get_embedding(summary)
    article_embedding = embeddings[0]
    article_embedding /= np.linalg.norm(article_embedding)  # 벡터 정규화

    return article_embedding, (common_analysis if is_analysis_created else {})


# 사용자 프로필 정보 임베딩 생성 함수
# 처음 회원가입할 때 및 기사 추천시 사용자 임베딩이 없을 때 호출
async def generate_user_profile_embedding(user: User) -> list[float]:
    # 사용자 프로필 정보를 자연스러운 구어체 문장형으로 묘사하여 초기 프로필 임베딩 생성
    profile_text = [
        f"이 사용자는 {user.age}세이며, 성별은 {user.gender.value}자입니다.",
        f"현재 직업은 {user.job.value}이며, 주로 {user.region.value} 지역의 소식에 관심이 있습니다.",
        f"평소에 {user.interest.value} 분야의 뉴스를 즐겨 읽습니다.",
        f"뉴스를 읽는 주된 목적은 {user.purpose.value}입니다.",
        f"추가적인 사용자 성향 정보는 다음과 같습니다: {user.extra_information}",
    ]
    embeddings = await get_embedding(
        profile_text
    )  # 각 프로필 항목에 대한 임베딩을 리스트로 반환

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
