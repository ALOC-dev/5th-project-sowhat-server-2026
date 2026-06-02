import json

from app.services.llm.groq_client import create_json_completion
from app.services.llm.prompts import (
    COMMON_ANALYSIS_PROMPT,
    PERSONAL_ANALYSIS_PROMPT,
    SYSTEM_JSON_PROMPT,
)


async def generate_common_analysis(article_data: dict):
    prompt = COMMON_ANALYSIS_PROMPT.format(
        title=article_data["title"],
        category=article_data["category"],
        content=article_data["content"],
    )

    response = await create_json_completion(
        [
            {"role": "system", "content": SYSTEM_JSON_PROMPT},
            {"role": "user", "content": prompt},
        ]
    )

    raw_text = response.choices[0].message.content.strip()

    raw_text = raw_text.replace("```json", "").replace("```", "").strip()

    print(raw_text)

    try:
        return json.loads(raw_text)

    except json.JSONDecodeError as exc:
        print(f"[JSON ERROR] {exc}")
        print(raw_text)

        return {
            "summary": "해설 생성 실패",
            "keyword": "오류",
        }


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

    response = await create_json_completion(
        [
            {"role": "system", "content": SYSTEM_JSON_PROMPT},
            {"role": "user", "content": prompt},
        ]
    )

    raw_text = response.choices[0].message.content.strip()

    raw_text = raw_text.replace("```json", "").replace("```", "").strip()

    print(raw_text)

    try:
        return json.loads(raw_text)

    except json.JSONDecodeError as exc:
        print(f"[JSON ERROR] {exc}")
        print(raw_text)

        return {
            "effect": "해설 생성 실패",
            "solution": "잠시 후 다시 시도해주세요.",
        }
