from pydantic import BaseModel

# from app.models.user_info import GenderEnum, RegionEnum, JobEnum, InterestEnum


# 회원가입, 정보 수정 요청에서 입력하는 정보만
class ProfileBase(BaseModel):
    age: int
    gender: str
    region: str
    job: str
    interest: str

    """
    gender: GenderEnum
    region: RegionEnum
    job: JobEnum
    interest: InterestEnum
    """


# 회원가입 요청
class ProfileCreateRequest(ProfileBase):
    pass


# 정보수정 요청
class ProfileUpdateRequest(ProfileBase):
    pass


# 프로필 조회 응답 (id까지 포함된 버전)
class ProfileGetResponse(ProfileBase):
    user_id: int


# 회원가입 응답
class ProfileCreateResponse(BaseModel):
    user_id: int
    message: str = "회원가입이 완료되었습니다."


# 프로필 수정 시 응답 (최신 정보 포함)
class ProfileUpdateResponse(BaseModel):
    user_id: int
    updated_data: ProfileBase
