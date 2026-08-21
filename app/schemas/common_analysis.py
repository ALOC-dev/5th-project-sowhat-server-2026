from typing import Optional
from pydantic import BaseModel, ConfigDict


# 핵심 용어 1개 (용어 + 뜻 설명)
# OpenAI structured output(strict)은 임의 키 dict를 허용하지 않아
# LLM 응답은 리스트로 받고, 이후 {word: description} dict로 변환해 사용한다
class KeywordItem(BaseModel):
    word: str
    description: str


# 공통 해설 생성 시 JSON 형식 맞추기 위한 객체
class CommonAnalysis(BaseModel):
    success: bool = True  # 기사 DB에 추가할 경우 True
    category: Optional[str] = None  # 카테고리는 선택적 반환
    summary: str
    keyword: list[KeywordItem]

    # DB 객체(ORM)를 바로 Pydantic 모델로 변환할 수 있게 설정
    model_config = ConfigDict(from_attributes=True)
