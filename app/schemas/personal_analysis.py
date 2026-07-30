from pydantic import BaseModel, ConfigDict


# 링크 검색 결과 (제목, URL)
class Link(BaseModel):
    title: str
    url: str

    # DB 객체(ORM)를 바로 Pydantic 모델로 변환할 수 있게 설정
    model_config = ConfigDict(from_attributes=True)


# DB 및 최종 웹 응답 반환용 (링크 제목과 URL 제공)
class PersonalAnalysis(BaseModel):
    effect: str
    solution: str
    links: list[Link] = []

    # DB 객체(ORM)를 바로 Pydantic 모델로 변환할 수 있게 설정
    model_config = ConfigDict(from_attributes=True)


# 1차 LLM 해설 생성용 (검색어로 찾을 링크 이름 포함)
# 주소(URL)는 LLM이 지어낼 위험이 있어 받지 않고, 창구 이름만 받는다
class PersonalAnalysisBeforeSearch(BaseModel):
    effect: str
    solution: str
    link_names: list[str] = []

    # DB 객체(ORM)를 바로 Pydantic 모델로 변환할 수 있게 설정
    model_config = ConfigDict(from_attributes=True)
