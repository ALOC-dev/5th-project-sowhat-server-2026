# app/services/llm_service.py

import json
from groq import AsyncGroq
from app.core.config import settings

client = AsyncGroq(api_key=settings.GROQ_API_KEY)

SYSTEM_PROMPT = """
너는 뉴스 해설 서비스의 분석기다.
반드시 아래 JSON 형식으로만 답해라.

{
  "summary": "기사 핵심 요약",
  "impact": "이 뉴스가 사용자에게 어떤 영향을 줄 수 있는지",
  "action": "사용자가 취할 수 있는 대응"
}
""".strip()

async def analyze_article_with_groq(title: str, content: str, category: str | None = None):
    user_prompt = f"""
제목: {title}
카테고리: {category or "미분류"}
본문:
{content}
""".strip()

    response = await client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )

    raw_text = response.choices[0].message.content.strip()
    return json.loads(raw_text)