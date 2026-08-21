from typing import Optional
from pydantic import BaseModel, ConfigDict


# 사용자 정보 필터링 결과를 받는 데 사용하는 객체
class FilteredExtraInformation(BaseModel):
    success: bool
    summary: Optional[str] = None

    # DB 객체(ORM)를 바로 Pydantic 모델로 변환할 수 있게 설정
    model_config = ConfigDict(from_attributes=True)
