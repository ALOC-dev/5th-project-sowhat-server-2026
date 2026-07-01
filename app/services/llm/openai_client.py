from openai import AsyncOpenAI
from app.core.config import settings

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


def create_json_completion(messages, response_format):
    return client.chat.completions.parse(
        model=settings.OPENAI_COMPLETION_MODEL,
        messages=messages,
        response_format=response_format,
    )


async def get_embedding(text):
    response = await client.embeddings.create(
        model=settings.OPENAI_EMBEDDING_MODEL,
        input=text,
    )
    return response.data[0].embedding
