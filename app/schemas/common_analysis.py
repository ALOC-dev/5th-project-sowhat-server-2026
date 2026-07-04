from pydantic import BaseModel, ConfigDict


# 공통 해설 생성 시 JSON 형식 맞추기 위한 객체
class CommonAnalysis(BaseModel):
    summary: str
    keyword: str

    # DB 객체(ORM)를 바로 Pydantic 모델로 변환할 수 있게 설정
    model_config = ConfigDict(from_attributes=True)
