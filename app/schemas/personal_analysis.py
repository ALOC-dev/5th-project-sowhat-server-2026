from pydantic import BaseModel, ConfigDict


# LLM 응답 형식
# 주소(URL)는 LLM이 지어낼 위험이 있어 받지 않고, 등록된 창구 이름만 받는다
class PersonalAnalysis(BaseModel):
    effect: str
    solution: str
    link_name: str = ""

    # DB 객체(ORM)를 바로 Pydantic 모델로 변환할 수 있게 설정
    model_config = ConfigDict(from_attributes=True)


# API 응답 형식
# link는 link_name을 서버에서 등록된 주소로 변환한 값이다
class PersonalAnalysisResponse(PersonalAnalysis):
    link: str = ""
