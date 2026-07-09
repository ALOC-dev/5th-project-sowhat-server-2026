# ── POST /api/auth/signup 테스트 ──────────────────────────────

import pytest

import app.services.user as user_service

SIGNUP_PAYLOAD = {
    "email": "test@example.com",
    "password": "password123",
    "age": 25,
    "gender": "MALE",
    "region": "SEOUL",
    "job": "STUDENT",
    "interest": "ECONOMY",
    "purpose": "STUDY",
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


def test_signup_duplicate_email(client):
    client.post("/api/auth/signup", json=SIGNUP_PAYLOAD)
    response = client.post("/api/auth/signup", json=SIGNUP_PAYLOAD)

    assert response.status_code == 409
    error = response.json()["error"]
    assert error["code"] == "DuplicateEmailError"
    assert error["message"] == "이미 가입된 이메일입니다."


def test_signup_invalid_email(client):
    payload = {**SIGNUP_PAYLOAD, "email": "not-an-email"}
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
