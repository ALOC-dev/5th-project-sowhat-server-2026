from pydantic import BaseModel


class ArticleListItem(BaseModel):
    article_id: int
    title: str
    date: str
    content_preview: str
    category: str