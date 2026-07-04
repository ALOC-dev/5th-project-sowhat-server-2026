# import json
# from app.services.llm.groq_client import create_json_completion
from app.services.llm.openai_client import create_json_completion, get_embedding
from app.services.llm.prompts import (
    COMMON_ANALYSIS_PROMPT,
    PERSONAL_ANALYSIS_PROMPT,
    SYSTEM_JSON_PROMPT,
)

from app.schemas.common_analysis import CommonAnalysis
from app.schemas.personal_analysis import PersonalAnalysis


async def generate_common_analysis(article_data: dict):
    prompt = COMMON_ANALYSIS_PROMPT.format(
        title=article_data["title"],
        category=article_data["category"],
        content=article_data["content"],
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

    parsed["embedding"] = await get_embedding(parsed["summary"])

    """
    returns: dict
        {
            "summary": str,
            "embedding": list[float],
        }
    """
    return parsed


async def generate_personal_analysis(
    article_data: dict,
    user_profile: dict,
):
    prompt = PERSONAL_ANALYSIS_PROMPT.format(
        title=article_data["title"],
        category=article_data["category"],
        content=article_data["content"],
        age=user_profile["age"],
        gender=user_profile["gender"],
        region=user_profile["region"],
        job=user_profile["job"],
        interest=user_profile["interest"],
        purpose=user_profile["purpose"],
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
    return parsed


async def generate_user_profile_embedding(user):
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

    return embeddings
