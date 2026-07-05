# import json
import numpy as np

# from app.services.llm.groq_client import create_json_completion
from app.models.article import Article
from app.models.user import User
from app.services.llm.openai_client import create_json_completion, get_embedding
from app.services.llm.prompts import (
    COMMON_ANALYSIS_PROMPT,
    PERSONAL_ANALYSIS_PROMPT,
    SYSTEM_JSON_PROMPT,
)

from app.schemas.common_analysis import CommonAnalysis
from app.schemas.personal_analysis import PersonalAnalysis


async def generate_common_analysis(article: Article | dict) -> dict:
    if type(article) is Article:
        article = article.model_dump()

    prompt = COMMON_ANALYSIS_PROMPT.format(
        title=article["title"],
        category=article["category"],
        content=article["content"],
    )

    ### Groq
    # response = await groq_client.create_json_completion(
    #     [
    #         {"role": "system", "content": SYSTEM_JSON_PROMPT},
    #         {"role": "user", "content": prompt},
    #     ]
    # )
    # raw_text = response.choices[0].message.content.strip()

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
            # TODO: "keyword": dict(str, str) 추가
        }
    """
    return parsed


async def generate_personal_analysis(article: Article, user: User) -> dict:
    prompt = PERSONAL_ANALYSIS_PROMPT.format(
        title=article.title,
        category=article.category,
        content=article.content,
        age=user.age,
        gender=user.gender,
        region=user.region,
        job=user.job,
        interest=user.interest,
        purpose=user.purpose,
    )

    ### Groq
    # response = await create_json_completion(
    #     [
    #         {"role": "system", "content": SYSTEM_JSON_PROMPT},
    #         {"role": "user", "content": prompt},
    #     ]
    # )
    # raw_text = response.choices[0].message.content.strip()

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


# 기사 임베딩 생성 함수
# LLM으로 생성된 기사 요약본을 통해 임베딩 생성
async def generate_article_embedding(article: Article | dict) -> list[float]:
    if type(article) is Article:
        article = article.model_dump()

    # 기사 요약 불러오기, 없을 시 생성
    if article["summary"] is None:
        common_analysis = await generate_common_analysis(article)
        summary = common_analysis["summary"]
    else:
        summary = article["summary"]

    embeddings = await get_embedding(summary)
    article_embedding = embeddings[0]
    article_embedding /= np.linalg.norm(article_embedding)  # 벡터 정규화
    return article_embedding


# 사용자 프로필 정보 임베딩 생성 함수
# 처음 회원가입할 때 및 기사 추천시 사용자 임베딩이 없을 때 호출
async def generate_user_profile_embedding(user: User) -> list[float]:
    # 사용자 프로필 정보를 자연스러운 구어체 문장형으로 묘사하여 초기 프로필 임베딩 생성
    profile_text = [
        f"이 사용자는 {user.age}세이며, 성별은 {user.gender}입니다.",
        f"현재 직업은 {user.job}이며, 주로 {user.region} 지역의 소식에 관심이 있습니다.",
        f"평소에 {user.interest} 분야의 뉴스를 즐겨 읽습니다.",
        f"뉴스를 읽는 주된 목적은 {user.purpose}입니다.",
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

    print("TYPE:", type(profile_embedding))

    return profile_embedding
