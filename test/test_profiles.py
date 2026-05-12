# ── POST /profiles 테스트 ──────────────────────────────────


def test_create_profile_success(client):
    payload = {
        "age": 20,
        "gender": "MALE",
        "region": "SEOUL",
        "job": "STUDENT",
        "interest": "ECONOMY",
    }

    response = client.post("/api/profiles", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert "user_id" in data


# ── GET /profiles/{user_id} 테스트 ──────────────────────────


def test_get_profile_success(client):
    # 1. 테스트용 데이터 생성
    setup_payload = {
        "age": 25,
        "gender": "FEMALE",
        "region": "BUSAN",
        "job": "OFFICE_WORKER",
        "interest": "POLITICS",
    }
    create_res = client.post("/api/profiles", json=setup_payload)
    created_user_id = create_res.json()["user_id"]

    # 2. 방금 만든 데이터 조회
    response = client.get(f"/api/profiles/{created_user_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["region"] == "BUSAN"
    assert data["job"] == "OFFICE_WORKER"


def test_get_profile_not_found(client):
    # 사용자가 존재하지 않는 경우
    response = client.get("/api/profiles/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "사용자를 찾을 수 없습니다."


# ── PATCH /profiles/{user_id} 테스트 ──────────────────────────


def test_modify_profile_success(client):
    # 1. 테스트용 데이터 생성
    setup_payload = {
        "age": 20,
        "gender": "MALE",
        "region": "SEOUL",
        "job": "STUDENT",
        "interest": "ECONOMY",
    }
    create_res = client.post("/api/profiles", json=setup_payload)
    created_user_id = create_res.json()["user_id"]

    # 2. 나이 수정
    update_payload = {"age": 25}
    response = client.patch(f"/api/profiles/{created_user_id}", json=update_payload)

    assert response.status_code == 200
    assert response.json()["age"] == 25


def test_modify_profile_not_found(client):
    # 존재하지 않는 사용자의 정보 수정 시도
    update_payload = {"age": 25}
    response = client.patch(f"/api/profiles/999", json=update_payload)

    assert response.status_code == 404
    assert response.json()["detail"] == "사용자를 찾을 수 없습니다."
