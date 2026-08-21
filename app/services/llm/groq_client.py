from groq import AsyncGroq
from app.core.config import settings

client = AsyncGroq(api_key=settings.GROQ_API_KEY)


async def create_json_completion(messages: list[dict]) -> str:
    return await client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=messages,
        temperature=0.2,
        response_format={"type": "json_object"},
    )
