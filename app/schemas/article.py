from pydantic import BaseModel


class ArticleListItem(BaseModel):
    article_id: int
    title: str
    date: str
    content_preview: str
    category: str


class ArticleDetailResponse(BaseModel):
    article_id: int
    title: str
    date: str
    content: str
    category: str
    summary: str
    terms: str