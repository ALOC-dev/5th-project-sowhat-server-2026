import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import articles, users
from app.services.schedule import run_yonhap_crawling

# API 요청이 허용된 다른 origin 목록
CORS_ALLOW_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버 시작 시 실행
    crawling_task = asyncio.create_task(run_yonhap_crawling())

    yield  # 여기서부터 서버 시작

    # 서버 종료 시 실행
    crawling_task.cancel()


app = FastAPI(lifespan=lifespan)  # 앱 생성

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(articles.router)
app.include_router(users.router)


@app.get("/health")
def health():
    return {"status": "ok"}  # 서버 정상 동작 여부 확인용
