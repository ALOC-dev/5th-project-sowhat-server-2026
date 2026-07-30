from pydantic import BaseModel, ConfigDict


# 검색 결과 중 선택한 인덱스 및 관련도 점수 반환
class SelectedIndex(BaseModel):
    index: int
    score: int

    # DB 객체(ORM)를 바로 Pydantic 모델로 변환할 수 있게 설정
    model_config = ConfigDict(from_attributes=True)


# 링크 검색 결과 (제목, URL)
class Link(BaseModel):
    title: str
    url: str

    model_config = ConfigDict(from_attributes=True)


# DB 및 최종 웹 응답 반환용 (링크 제목과 URL 제공)
class PersonalAnalysis(BaseModel):
    effect: str
    solution: str
    links: list[Link] = []

    model_config = ConfigDict(from_attributes=True)


# 1차 LLM 해설 생성용 (검색어로 찾을 링크 이름 포함)
# 주소(URL)는 LLM이 지어낼 위험이 있어 받지 않고, 창구 이름만 받는다
class PersonalAnalysisBeforeSearch(BaseModel):
    effect: str
    solution: str
    link_names: list[str] = []

    model_config = ConfigDict(from_attributes=True)
