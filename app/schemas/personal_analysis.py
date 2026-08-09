from pydantic import BaseModel, ConfigDict

from app.models.enums import CategoryEnum


# 검색 결과 중 선택한 인덱스 및 관련도 점수 반환
class LinkSelectionResult(BaseModel):
    success: bool
    index: int
    score: int

    # DB 객체(ORM)를 바로 Pydantic 모델로 변환할 수 있게 설정
    model_config = ConfigDict(from_attributes=True)


# 링크 검색 결과 (제목, URL)
class Link(BaseModel):
    title: str
    url: str

    model_config = ConfigDict(from_attributes=True)


# 유사 기사 응답용
class SimilarArticle(BaseModel):
    title: str
    publisher: str
    source_url: str

    model_config = ConfigDict(from_attributes=True)


# DB 및 최종 웹 응답 반환용 (링크 제목과 URL 제공)
class PersonalAnalysis(BaseModel):
    effect: str
    solution: str
    links: list[Link] = []
    similar_articles: list[SimilarArticle] = []

    model_config = ConfigDict(from_attributes=True)


# 조회한 기사 목록 응답용
# 목록 UI가 쓰는 건 이 세 가지뿐이라 해설 본문(effect, solution, links)은 내보내지 않는다
class ViewedArticleResponse(BaseModel):
    article_id: int
    title: str
    category: CategoryEnum

    model_config = ConfigDict(from_attributes=True)


# 1차 LLM 해설 생성용 (검색어로 찾을 링크 이름 포함)
# 주소(URL)는 LLM이 지어낼 위험이 있어 받지 않고, 창구 이름만 받는다
# 1차 LLM 해설 생성용 (검색할 기관·서비스와 목적 포함)
# 주소(URL)는 LLM이 지어낼 위험이 있어 받지 않는다
class LinkSearchTarget(BaseModel):
    source_name: str
    search_purpose: str


class PersonalAnalysisBeforeSearch(BaseModel):
    effect: str
    solution: str
    link_targets: list[LinkSearchTarget] = []

    model_config = ConfigDict(from_attributes=True)


# Tavily 검색 결과 중 2차 LLM이 선택한 결과
class LinkSelectionResult(BaseModel):
    success: bool
    index: int | None = None
    score: int | None = None
