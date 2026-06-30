from datetime import datetime
from pydantic import BaseModel


class ArticlePreviewResponse(BaseModel):
    id: int
    title: str
    published_at: datetime
    publisher: str
    content: str
    category: str


class ArticleDetailResponse(BaseModel):
    id: int
    title: str
    source_url: str
    published_at: datetime
    publisher: str
    reporter: str
    category: str
    content: str
    summary: str
    embedding: list[float]
