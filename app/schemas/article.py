from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ArticlePreviewResponse(BaseModel):
    id: int
    title: str
    published_at: datetime
    publisher: str
    content: str
    category: str

    # DB 객체(ORM)를 바로 Pydantic 모델로 변환할 수 있게 설정
    model_config = ConfigDict(from_attributes=True)


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
    # [{"word": "단어", "description": "뜻 설명"}] 형태의 키워드 JSON
    keyword: list[dict[str, str]] | None = None

    # DB 객체(ORM)를 바로 Pydantic 모델로 변환할 수 있게 설정
    model_config = ConfigDict(from_attributes=True)
