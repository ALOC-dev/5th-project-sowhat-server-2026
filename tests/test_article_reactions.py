from datetime import datetime

import pytest

from app.core.security import create_access_token
from app.models.article import Article
from app.models.enums import CategoryEnum, UserResponseEnum
from app.models.personal_analysis import PersonalAnalysis
from app.models.user import User
from tests.conftest import TestingSessionLocal


def create_reaction_target(
    client,
    *,
    authenticate: bool = True,
    with_analysis: bool = True,
    user_response: UserResponseEnum | None = None,
) -> tuple[int, int]:
    db = TestingSessionLocal()
    try:
        user = User(
            login_id="reaction-user",
            hashed_password="not-used",
            username="reaction user",
            age=20,
        )
        article = Article(
            title="reaction article",
            source_url="https://example.com/reaction-article",
            published_at=datetime(2026, 8, 14),
            publisher="test publisher",
            reporter="test reporter",
            category=CategoryEnum.ECONOMY,
            content="article content",
        )
        db.add_all([user, article])
        db.commit()
        db.refresh(user)
        db.refresh(article)

        if with_analysis:
            db.add(
                PersonalAnalysis(
                    article_id=article.id,
                    user_id=user.id,
                    effect="effect",
                    solution="solution",
                    title=article.title,
                    category=article.category,
                    user_response=user_response,
                )
            )
            db.commit()

        if authenticate:
            client.cookies.set("access_token", create_access_token(user.id))

        return user.id, article.id
    finally:
        db.close()


@pytest.mark.parametrize(
    "user_response",
    [UserResponseEnum.GOOD, UserResponseEnum.BAD],
)
def test_submit_analysis_reaction_saves_response(client, user_response):
    user_id, article_id = create_reaction_target(client)

    response = client.post(
        f"/api/articles/{article_id}/analysis/reaction",
        json={"user_response": user_response.value},
    )

    assert response.status_code == 200
    assert response.json() == {
        "article_id": article_id,
        "user_response": user_response.value,
    }

    db = TestingSessionLocal()
    try:
        analysis = (
            db.query(PersonalAnalysis)
            .filter(
                PersonalAnalysis.user_id == user_id,
                PersonalAnalysis.article_id == article_id,
            )
            .one()
        )
        assert analysis.user_response == user_response
    finally:
        db.close()


def test_submit_analysis_reaction_changes_previous_response(client):
    _, article_id = create_reaction_target(
        client, user_response=UserResponseEnum.GOOD
    )

    response = client.post(
        f"/api/articles/{article_id}/analysis/reaction",
        json={"user_response": UserResponseEnum.BAD.value},
    )

    assert response.status_code == 200
    assert response.json()["user_response"] == UserResponseEnum.BAD.value


def test_submit_analysis_reaction_rejects_invalid_response(client):
    _, article_id = create_reaction_target(client)

    response = client.post(
        f"/api/articles/{article_id}/analysis/reaction",
        json={"user_response": "neutral"},
    )

    assert response.status_code == 422


def test_submit_analysis_reaction_requires_login(client):
    _, article_id = create_reaction_target(client, authenticate=False)

    response = client.post(
        f"/api/articles/{article_id}/analysis/reaction",
        json={"user_response": UserResponseEnum.GOOD.value},
    )

    assert response.status_code == 401


def test_submit_analysis_reaction_requires_personal_analysis(client):
    _, article_id = create_reaction_target(client, with_analysis=False)

    response = client.post(
        f"/api/articles/{article_id}/analysis/reaction",
        json={"user_response": UserResponseEnum.GOOD.value},
    )

    assert response.status_code == 404

