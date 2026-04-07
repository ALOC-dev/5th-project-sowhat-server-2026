from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from app.routers import articles, profiles

from app.routers.articles import router as articles_router

app = FastAPI()



@app.get("/")
def read_root():
    return {"message": "FastAPI server is running"}

app.include_router(articles.router, profiles.router)  # 라우터 등록


@app.get("/health")
def health():
    return {"status": "ok"}


profiles = []

# 임시 프로필 데이터
class ProfileCreate(BaseModel):
    region: str
    interests: List[str]
    age_group: str


@app.post("/profiles")
def create_profile(profile: ProfileCreate):
    new_profile = {
        "id": len(profiles) + 1,
        "region": profile.region,
        "interests": profile.interests,
        "age_group": profile.age_group,
    }
    profiles.append(new_profile)
    return {"message": "profile created", "data": new_profile}


@app.get("/profiles")
def get_profiles():
    return profiles


app.include_router(articles_router)
    return {"status": "ok"}  # 서버 정상 동작 여부 확인용