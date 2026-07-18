from datetime import datetime, timedelta

import pytest
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.services.schedule import process_yonhap_rss, YONHAP_RSS
from app.crud.article import get_highest_similarity, get_article_by_source_url

categories = [
    "연합뉴스(산업/IT)",
    "연합뉴스(정치)",
    "연합뉴스(경제)",
    "연합뉴스(사회)",
    "연합뉴스(세계)",
]

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


async def test_irrelevant_articles():
    db = TestingSessionLocal()

    test_category = 0
    threshold = 0.1

    results = await process_yonhap_rss(
        category_name=categories[test_category],
        rss_url=YONHAP_RSS[categories[test_category]],
        max_articles=10,
        db=db,
    )

    for i in range(len(results)):
        r = results[i]

        if r["embedding"] is not None:
            article = get_article_by_source_url(db, r["source_url"])

            highest_similarity = get_highest_similarity(
                db,
                datetime.now() - timedelta(hours=24),
                article.id,
                article.embedding,
            )

            print(f"[LOG {i}]  유사도: " + str(highest_similarity))

            distance = 1 - highest_similarity
            if distance <= threshold:
                print(f"[SKIP {i}] 유사한 기사")
                continue

    db.close()
