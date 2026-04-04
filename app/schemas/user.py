from pydantic import BaseModel


class ProfileCreate(BaseModel):
    age: int
    gender: str
    region: str
    job: str
    interest: str


class ProfileResponse(BaseModel):
    user_id: int
    age: int
    gender: str
    region: str
    job: str
    interest: str
    success: bool
