from fastapi import FastAPI
from app.routers import articles, profiles

app = FastAPI()  # 앱 생성

app.include_router(articles.router, profiles.router)  # 라우터 등록


@app.get("/health")
def health():
    return {"status": "ok"}  # 서버 정상 동작 여부 확인용
