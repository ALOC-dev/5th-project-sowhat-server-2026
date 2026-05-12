from pydantic import BaseModel, ConfigDict
from typing import Optional

from app.models.enums import GenderEnum, RegionEnum, JobEnum, InterestEnum


# 회원가입, 정보 수정 요청에서 입력하는 정보만
class ProfileBase(BaseModel):
    age: int
    gender: GenderEnum
    region: RegionEnum
    job: JobEnum
    interest: InterestEnum

    # DB 객체(ORM)를 바로 Pydantic 모델로 변환할 수 있게 설정
    model_config = ConfigDict(from_attributes=True)


# 회원가입 요청
class ProfileCreateRequest(ProfileBase):
    pass


# 정보수정 요청 (모든 필드를 선택적으로 변경 - Optional)
class ProfileUpdateRequest(ProfileBase):
    age: Optional[int] = None
    gender: Optional[GenderEnum] = None
    region: Optional[RegionEnum] = None
    job: Optional[JobEnum] = None
    interest: Optional[InterestEnum] = None


# 프로필 조회 응답 (id까지 포함된 버전)
class ProfileGetResponse(ProfileBase):
    user_id: int


# 회원가입 응답
class ProfileCreateResponse(BaseModel):
    user_id: int
    message: str = "회원가입이 완료되었습니다."


# 프로필 수정 시 응답 (최신 정보 포함)
class ProfileUpdateResponse(ProfileBase):
    user_id: int
