# ── /api/users 프로필 CRUD 테스트 ──────────────────────────────

import pytest

import app.services.user as user_service

USER_PAYLOAD = {
    "age": 20,
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


# ── POST /api/users ─────────────────────────────────────────


def test_create_user_success(client):
    response = client.post("/api/users", json=USER_PAYLOAD)

    assert response.status_code == 201
    assert "id" in response.json()


# ── /api/users/me (JWT 인증) ────────────────────────────────

SIGNUP_PAYLOAD = {
    **USER_PAYLOAD,
    "email": "test@example.com",
    "password": "test-password",
}


# 회원가입 후 로그인해 인증 쿠키가 담긴 client를 돌려준다
def signup_and_login(client):
    signup = client.post("/api/auth/signup", json=SIGNUP_PAYLOAD)
    assert signup.status_code == 201

    login = client.post(
        "/api/auth/login",
        json={
            "email": SIGNUP_PAYLOAD["email"],
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
    assert data["region"] == "SEOUL"
    assert data["job"] == "STUDENT"


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
