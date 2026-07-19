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


# ── GET /api/users/{user_id} ────────────────────────────────


def test_get_user_success(client):
    created_id = client.post("/api/users", json=USER_PAYLOAD).json()["id"]

    response = client.get(f"/api/users/{created_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["region"] == "SEOUL"
    assert data["job"] == "STUDENT"


def test_get_user_not_found(client):
    response = client.get("/api/users/999")

    assert response.status_code == 404
    assert response.json()["error"]["message"] == "사용자를 찾을 수 없습니다."


# ── PATCH /api/users/{user_id} ──────────────────────────────


def test_update_user_success(client):
    created_id = client.post("/api/users", json=USER_PAYLOAD).json()["id"]

    response = client.patch(f"/api/users/{created_id}", json={"age": 25})

    assert response.status_code == 200
    assert response.json()["age"] == 25


def test_update_user_not_found(client):
    response = client.patch("/api/users/999", json={"age": 25})

    assert response.status_code == 404
    assert response.json()["error"]["message"] == "사용자를 찾을 수 없습니다."
