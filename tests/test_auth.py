# ── POST /api/auth/signup 테스트 ──────────────────────────────

import pytest

import app.services.user as user_service

SIGNUP_PAYLOAD = {
    "login_id": "testuser",
    "username": "테스트",
    "password": "password123",
    "age": 25,
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


def test_signup_success(client):
    response = client.post("/api/auth/signup", json=SIGNUP_PAYLOAD)

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["message"] == "회원가입이 완료되었습니다."


def test_signup_duplicate_login_id(client):
    client.post("/api/auth/signup", json=SIGNUP_PAYLOAD)
    response = client.post("/api/auth/signup", json=SIGNUP_PAYLOAD)

    assert response.status_code == 409
    error = response.json()["error"]
    assert error["code"] == "DuplicateLoginIdError"


def test_signup_missing_login_id(client):
    payload = {k: v for k, v in SIGNUP_PAYLOAD.items() if k != "login_id"}
    response = client.post("/api/auth/signup", json=payload)

    assert response.status_code == 422


def test_signup_short_password(client):
    payload = {**SIGNUP_PAYLOAD, "password": "short"}
    response = client.post("/api/auth/signup", json=payload)

    assert response.status_code == 422


def test_signup_password_is_hashed(client):
    from tests.conftest import TestingSessionLocal
    from app.models.user import User

    response = client.post("/api/auth/signup", json=SIGNUP_PAYLOAD)
    user_id = response.json()["id"]

    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        assert user.hashed_password != SIGNUP_PAYLOAD["password"]
        assert user.hashed_password.startswith("$2b$")
    finally:
        db.close()
