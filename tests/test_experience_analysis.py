import pytest
from fastapi.testclient import TestClient

from app.main import app

TEST_ANALYSIS_PAYLOAD = {
    "article_id": 1400,
    "age_group": "20대",
    "job": "경영·사업",
    "interest": "경제",
}


# 이 테스트 파일은 conftest의 Mock DB(client)가 아니라 실제 DB(SessionLocal)를 그대로 사용한다.
# get_db를 오버라이드하지 않으므로 app.dependency_overrides가 비어 있어야 한다.
@pytest.fixture
def real_db_client(monkeypatch):
    async def no_crawling(*args, **kwargs):
        return None

    monkeypatch.setattr("app.main.start_crawling_thread", no_crawling)

    with TestClient(app) as test_client:
        yield test_client


# 해설 만들기, 만들어진 해설 불러오기
def test_get_experience_analysis(real_db_client):
    client = real_db_client

    response = client.get(
        "/api/articles/%s/analysis/experience?age-group=%s&job=%s&interest=%s"
        % (
            TEST_ANALYSIS_PAYLOAD["article_id"],
            TEST_ANALYSIS_PAYLOAD["age_group"],
            TEST_ANALYSIS_PAYLOAD["job"],
            TEST_ANALYSIS_PAYLOAD["interest"],
        )
    )
    assert response.status_code == 200

    # 만들어진 해설 조회
    response = client.get(
        "/api/articles/%s/analysis/experience?age-group=%s&job=%s&interest=%s"
        % (
            TEST_ANALYSIS_PAYLOAD["article_id"],
            TEST_ANALYSIS_PAYLOAD["age_group"],
            TEST_ANALYSIS_PAYLOAD["job"],
            TEST_ANALYSIS_PAYLOAD["interest"],
        )
    )
    assert response.status_code == 200
