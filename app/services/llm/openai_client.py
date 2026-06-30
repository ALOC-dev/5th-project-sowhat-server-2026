from openai import AsyncOpenAI
from app.core.config import settings

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


def create_json_completion(messages):
    return client.responses.create(
        model=settings.OPENAI_MODEL,
        input=messages,
    )
