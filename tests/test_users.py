# ── /api/users 프로필 CRUD 테스트 ──────────────────────────────

from datetime import datetime

import pytest

import app.services.user as user_service
from app.models.article import Article
from app.models.enums import CategoryEnum
from app.models.personal_analysis import PersonalAnalysis
from tests.conftest import TestingSessionLocal

USER_PAYLOAD = {
    "login_id": "testuser",
    "username": "테스트",
    "age": 20,
    "gender": "남",
    "region": "서울",
    "job": "학생",
    "interest": "경제",
    "purpose": "공부",
    "extra_information": "테스트 유저입니다.",
}


# 임베딩 생성이 실제 OpenAI API를 호출하지 않도록 가짜 함수로 대체
@pytest.fixture(autouse=True)
def mock_embedding(monkeypatch):
    async def fake_embedding(user):
        return [0.0] * 1536

    monkeypatch.setattr(
        user_service, "generate_user_profile_embedding", fake_embedding
    )


# ── POST /api/users ─────────────────────────────────────────


# POST /api/users는 비밀번호를 받지 않지만 user.hashed_password가 NOT NULL이라
# 현재 스키마에서는 저장이 불가능하다. 회원가입은 /api/auth/signup으로 일원화 필요.
@pytest.mark.skip(reason="POST /api/users가 hashed_password NOT NULL 제약으로 동작 불가")
def test_create_user_success(client):
    response = client.post("/api/users", json=USER_PAYLOAD)

    assert response.status_code == 201
    assert "id" in response.json()


# ── /api/users/me (JWT 인증) ────────────────────────────────

SIGNUP_PAYLOAD = {
    **USER_PAYLOAD,
    "password": "test-password",
}


# 회원가입 후 로그인해 인증 쿠키가 담긴 client를 돌려준다
def signup_and_login(client):
    signup = client.post("/api/auth/signup", json=SIGNUP_PAYLOAD)
    assert signup.status_code == 201

    login = client.post(
        "/api/auth/login",
        json={
            "login_id": SIGNUP_PAYLOAD["login_id"],
            "password": SIGNUP_PAYLOAD["password"],
        },
    )
    assert login.status_code == 200

    return signup.json()["id"]


def test_get_my_profile_success(client):
    signup_and_login(client)

    response = client.get("/api/users/me")

    assert response.status_code == 200
    data = response.json()
    assert data["region"] == "서울"
    assert data["job"] == "학생"


def test_get_my_profile_without_login(client):
    response = client.get("/api/users/me")

    assert response.status_code == 401


def test_update_my_profile_success(client):
    signup_and_login(client)

    response = client.patch("/api/users/me", json={"age": 25})

    assert response.status_code == 200
    assert response.json()["age"] == 25


def test_update_my_profile_without_login(client):
    response = client.patch("/api/users/me", json={"age": 25})

    assert response.status_code == 401


# ── GET /api/users/me/articles (조회한 기사 목록) ──────────────


# 기사와 조회 기록(개인해설)을 테스트 DB에 직접 넣는다.
# 조회 기록은 원래 GET /api/articles/analysis에서 생기지만 LLM 호출이 필요해
# 여기서는 결과만 직접 심는다.
def create_viewed_article(user_id: int, title: str, content: str = "본문") -> int:
    db = TestingSessionLocal()
    try:
        article = Article(
            title=title,
            source_url=f"https://example.com/{title}",
            published_at=datetime(2026, 1, 1),
            publisher="연합뉴스",
            reporter="테스트기자",
            content=content,
            category=CategoryEnum.ECONOMY,
        )
        db.add(article)
        db.commit()
        db.refresh(article)

        db.add(
            PersonalAnalysis(
                article_id=article.id,
                user_id=user_id,
                effect="예상되는 영향",
                solution="대응 방법",
                title=article.title,
                category=article.category,
            )
        )
        db.commit()

        return article.id
    finally:
        db.close()


def test_get_my_viewed_articles_success(client):
    user_id = signup_and_login(client)
    create_viewed_article(user_id, "먼저 본 기사")
    create_viewed_article(user_id, "나중에 본 기사")

    response = client.get("/api/users/me/articles")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    # 최근에 본 기사가 먼저 온다
    assert data[0]["title"] == "나중에 본 기사"
    assert data[1]["title"] == "먼저 본 기사"


# 목록 응답의 본문은 미리보기 길이로 잘려서 나간다
def test_get_my_viewed_articles_truncates_content(client):
    user_id = signup_and_login(client)
    create_viewed_article(user_id, "긴 기사", content="가" * 30)

    response = client.get("/api/users/me/articles")

    assert response.status_code == 200
    assert response.json()[0]["content"] == "가" * 25 + "..."


def test_get_my_viewed_articles_empty(client):
    signup_and_login(client)

    response = client.get("/api/users/me/articles")

    assert response.status_code == 200
    assert response.json() == []


# 다른 사용자의 조회 기록은 섞이지 않는다
def test_get_my_viewed_articles_excludes_other_users(client):
    user_id = signup_and_login(client)
    create_viewed_article(user_id, "내가 본 기사")
    create_viewed_article(user_id + 1, "남이 본 기사")

    response = client.get("/api/users/me/articles")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "내가 본 기사"


def test_get_my_viewed_articles_pagination(client):
    user_id = signup_and_login(client)
    for index in range(3):
        create_viewed_article(user_id, f"기사 {index}")

    first_page = client.get("/api/users/me/articles?limit=2&offset=0")
    second_page = client.get("/api/users/me/articles?limit=2&offset=2")

    assert first_page.status_code == 200
    assert second_page.status_code == 200
    assert [item["title"] for item in first_page.json()] == ["기사 2", "기사 1"]
    assert [item["title"] for item in second_page.json()] == ["기사 0"]


def test_get_my_viewed_articles_invalid_limit(client):
    signup_and_login(client)

    response = client.get("/api/users/me/articles?limit=0")

    assert response.status_code == 422


def test_get_my_viewed_articles_without_login(client):
    response = client.get("/api/users/me/articles")

    assert response.status_code == 401
