import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import get_db, Base

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
def client():

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
