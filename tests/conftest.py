import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import get_db, Base
import app.services.search.tavily_client as tavily_client


# ── 0-1. 참고 링크 웹 검색 차단 ───────────────────────────────
# .env에 TAVILY_API_KEY가 있으면 개인해설 테스트가 실제 검색을 호출해
# 네트워크를 타고 API 크레딧까지 쓴다. 키 유무로 결과가 갈리지 않도록 기본 차단한다.
# 검색 동작을 확인하는 테스트는 get_client를 직접 대체해 쓴다.
@pytest.fixture(autouse=True)
def block_tavily_search(monkeypatch):
    monkeypatch.setattr(tavily_client, "get_client", lambda: None)


# ── 0. 외부 API 호출 테스트 실행 옵션 ─────────────────────────
# 연합뉴스 크롤링과 OpenAI 호출이 실제로 일어나는 테스트는 기본 실행에서 제외한다.
# 실행하려면 pytest에 --live 옵션을 준다.
def pytest_addoption(parser):
    parser.addoption(
        "--live",
        action="store_true",
        default=False,
        help="연합뉴스/OpenAI를 실제로 호출하는 테스트까지 실행한다",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--live"):
        return

    skip_live = pytest.mark.skip(reason="외부 API 호출 테스트. --live 옵션으로 실행")

    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip_live)


# ── 1. 인메모리 SQLite DB 설정 ────────────────────────────────
MOCK_DB_URL = "sqlite:///:memory:"  # Mock DB. 파일 대신 메모리에 DB 생성

engine = create_engine(
    MOCK_DB_URL,
    connect_args={"check_same_thread": False},  # SQLite 다중 스레드 접근 허용
    poolclass=StaticPool,  # 메모리 DB 연결 유지용
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ── 2. 테이블 자동 생성/삭제 Fixture ──────────────────────────
@pytest.fixture(autouse=True)
def setup_and_teardown_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# ── 3. TestClient 및 DB 오버라이드 Fixture ─────────────────────
@pytest.fixture
def client(monkeypatch):
    # 앱 시작(lifespan) 시 실제 크롤링이 돌지 않도록 무력화
    async def no_crawling(*args, **kwargs):
        return None

    monkeypatch.setattr("app.main.run_yonhap_crawling_periodically", no_crawling)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    # 기존 DB 의존성 설정을 무력화하고 Mock DB 넣기
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # 테스트 종료 후 오버라이드 초기화 (선택사항)
    app.dependency_overrides.clear()
