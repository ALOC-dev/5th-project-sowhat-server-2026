import json

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
