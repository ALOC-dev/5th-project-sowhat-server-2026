from pydantic import BaseModel, ConfigDict


class PersonalAnalysis(BaseModel):
    effect: str
    solution: str

    # DB 객체(ORM)를 바로 Pydantic 모델로 변환할 수 있게 설정
    model_config = ConfigDict(from_attributes=True)
