from pydantic import BaseModel


class ArticleResponse(BaseModel):
    article_id: int
    title: str
    date: str
    content: str
    category: str


class ArticleDetailResponse(BaseModel):
    article_id: int
    title: str
    date: str
    content: str
    category: str
    summary: str
    keyword: str
