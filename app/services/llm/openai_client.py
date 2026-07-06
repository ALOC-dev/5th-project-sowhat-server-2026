import numpy as np
from openai import AsyncOpenAI
from app.core.config import settings

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


def create_json_completion(messages: list[dict], response_format: type):
    return client.chat.completions.parse(
        model=settings.OPENAI_COMPLETION_MODEL,
        messages=messages,
        response_format=response_format,
    )


async def get_embedding(text: str | list[str]) -> list[list[float]]:
    response = await client.embeddings.create(
        model=settings.OPENAI_EMBEDDING_MODEL,
        input=text,
    )
    return [np.array(item.embedding) for item in response.data]
