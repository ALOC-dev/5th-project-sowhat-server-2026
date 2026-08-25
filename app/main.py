from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import articles, users, auth
from app.services.schedule import (
    start_crawling_thread,
)
from app.core.exceptions import register_exception_handlers

# API 요청이 허용된 다른 origin 목록
CORS_ALLOW_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://sowhat-news.vercel.app",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버 시작 시 실행
    start_crawling_thread(600)

    yield  # 여기서부터 서버 시작


app = FastAPI(lifespan=lifespan)  # 앱 생성

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth.router)
app.include_router(articles.router)
app.include_router(users.router)

# 예외 처리 핸들러 등록
register_exception_handlers(app)


@app.get("/health")
def health():
    return {"status": "ok"}  # 서버 정상 동작 여부 확인용


@app.middleware("http")
async def add_noindex(request, call_next):
    response = await call_next(request)
    response.headers["X-Robots-Tag"] = "noindex, nofollow"
    return response
