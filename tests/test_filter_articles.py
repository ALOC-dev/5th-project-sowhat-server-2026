from datetime import datetime, timedelta

import pytest
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base, SessionLocal
from app.services.llm.embedding_tasks import ensure_article_embedding
from app.services.schedule import process_yonhap_rss, YONHAP_RSS
from app.crud.article import (
    get_article_by_id,
    get_highest_similarity,
)

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


@pytest.mark.live
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
            highest_similarity = get_highest_similarity(
                db,
                datetime.now() - timedelta(hours=24),
                r["source_url"],
                r["embedding"],
            )

            print(f"[LOG {i}]  유사도: " + str(highest_similarity))

            distance = 1 - highest_similarity
            if distance <= threshold:
                print(f"[SKIP {i}] 유사한 기사")
                continue

    db.close()


async def test_delete_duplicate_articles():
    db = SessionLocal()

    test_ids = [1104, 1106, 1107, 1100, 1089, 1108]

    results = []

    for id in test_ids:
        await ensure_article_embedding(id)
        test_article = get_article_by_id(db, id)

        if test_article is None:
            print(f"[LOG {id}] 삭제된 기사")
            continue

        results.append(
            {
                "source_url": test_article.source_url,
                "embedding": test_article.embedding,
            }
        )

    print()

    for i in range(len(results)):
        r = results[i]

        if r["embedding"] is not None:
            highest_similarity = get_highest_similarity(
                db,
                datetime.now() - timedelta(hours=24),
                r["source_url"],
                r["embedding"],
            )

            print(f"[LOG {i}]  유사도: " + str(highest_similarity))

    db.close()
