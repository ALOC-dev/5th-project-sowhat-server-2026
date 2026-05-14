from pydantic import BaseModel
from app.models.enums import CategoryEnum

class ArticleResponse(BaseModel):
    article_id: int
    title: str
    date: str
    content: str
    category: CategoryEnum


class ArticleDetailResponse(BaseModel):
    article_id: int
    title: str
    date: str
    content: str
    category: str
    summary: str
    keyword: str
