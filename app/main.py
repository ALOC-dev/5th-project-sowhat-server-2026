import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routers import articles, profiles
from app.services.schedule import run_yonhap_crawling


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버 시작 시 실행
    crawling_task = asyncio.create_task(run_yonhap_crawling())

    yield  # 여기서부터 서버 시작

    # 서버 종료 시 실행
    crawling_task.cancel()


app = FastAPI(lifespan=lifespan)  # 앱 생성

# 라우터 등록
app.include_router(articles.router)
app.include_router(profiles.router)


@app.get("/health")
def health():
    return {"status": "ok"}  # 서버 정상 동작 여부 확인용
