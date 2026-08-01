# ── article_crud.create_articles 중복 처리 테스트 ─────────────

from datetime import datetime, timezone

import pytest
from sqlalchemy import StaticPool, create_engine, select
from sqlalchemy.orm import sessionmaker

from app.crud.article import create_articles
from app.db.database import Base
from app.models.article import Article
from app.models.enums import CategoryEnum

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


def make_payload(i: int) -> dict:
    return {
        "title": f"기사{i}",
        "source_url": f"https://www.yna.co.kr/view/AKR{i}",
        "published_at": datetime(2026, 7, 30, tzinfo=timezone.utc),
        "publisher": "연합뉴스",
        "reporter": "홍길동",
        "category": CategoryEnum.ECONOMY,
        "content": "본문",
    }


def stored_urls(db) -> set[str]:
    return {r for r in db.execute(select(Article.source_url)).scalars()}


def test_신규_기사_전량_저장(db):
    created = create_articles(db, [make_payload(i) for i in range(3)])

    assert len(created) == 3
    assert len(stored_urls(db)) == 3


# 배치 안에 이미 저장된 기사가 섞여 있어도 나머지는 저장돼야 한다.
# 예전 구현은 한 트랜잭션으로 묶어 저장해 중복 1건에 배치 전체가 롤백됐다.
def test_이미_저장된_기사가_섞여도_나머지는_저장된다(db):
    create_articles(db, [make_payload(0)])

    created = create_articles(db, [make_payload(i) for i in range(4)])

    assert len(created) == 3
    assert stored_urls(db) == {f"https://www.yna.co.kr/view/AKR{i}" for i in range(4)}


# 같은 수집 배치 안에 같은 기사가 두 번 들어와도 한 건만 저장되고 나머지는 살아야 한다.
def test_배치_내_중복은_한_건만_저장된다(db):
    payloads = [make_payload(0), make_payload(1), make_payload(0), make_payload(2)]

    created = create_articles(db, payloads)

    assert len(created) == 3
    assert len(stored_urls(db)) == 3


def test_중복만_있으면_빈_리스트를_반환한다(db):
    create_articles(db, [make_payload(0)])

    created = create_articles(db, [make_payload(0)])

    assert created == []
    assert len(stored_urls(db)) == 1
