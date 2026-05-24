from pydantic import BaseModel

# class ArticleResponse(BaseModel):
#     article_id: int
#     title: str
#     date: str
#     content: str
#     category: str


# 임시
class ArticleResponse(BaseModel):
    article_id: int
    title: str
    link: str
    content: str
    media: str


# class ArticleDetailResponse(BaseModel):
#     article_id: int
#     title: str
#     date: str
#     content: str
#     category: str
#     summary: str
#     keyword: str


# 임시
class ArticleDetailResponse(BaseModel):
    article_id: int
    title: str
    link: str
    content: str
    media: str
    category: str
    summary: str
    keyword: str
