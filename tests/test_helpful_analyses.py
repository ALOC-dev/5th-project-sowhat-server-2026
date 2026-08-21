from datetime import datetime

from app.core.security import create_access_token
from app.models.article import Article
from app.models.enums import CategoryEnum, UserResponseEnum
from app.models.personal_analysis import PersonalAnalysis
from app.models.user import User
from tests.conftest import TestingSessionLocal


def create_user(db, login_id: str) -> User:
    user = User(
        login_id=login_id,
        hashed_password="not-used",
        username=login_id,
        age=20,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_analysis(
    db,
    user_id: int,
    title: str,
    user_response: UserResponseEnum | None,
) -> int:
    article = Article(
        title=title,
        source_url=f"https://example.com/{title}",
        published_at=datetime(2026, 8, 14),
        publisher="test publisher",
        reporter="test reporter",
        category=CategoryEnum.ECONOMY,
        content="article content",
    )
    db.add(article)
    db.commit()
    db.refresh(article)

    db.add(
        PersonalAnalysis(
            article_id=article.id,
            user_id=user_id,
            effect="effect",
            solution="solution",
            title=title,
            category=CategoryEnum.ECONOMY,
            user_response=user_response,
        )
    )
    db.commit()
    return article.id


def authenticate(client, user_id: int) -> None:
    client.cookies.set("access_token", create_access_token(user_id))


def test_get_my_helpful_analyses_returns_only_my_good_responses(client):
    db = TestingSessionLocal()
    try:
        current_user = create_user(db, "current-user")
        other_user = create_user(db, "other-user")
        helpful_article_id = create_analysis(
            db, current_user.id, "helpful", UserResponseEnum.GOOD
        )
        create_analysis(db, current_user.id, "unhelpful", UserResponseEnum.BAD)
        create_analysis(db, current_user.id, "no-response", None)
        create_analysis(db, other_user.id, "other-user-helpful", UserResponseEnum.GOOD)
        authenticate(client, current_user.id)
    finally:
        db.close()

    response = client.get("/api/users/me/helpful-analyses")

    assert response.status_code == 200
    assert response.json() == [
        {
            "article_id": helpful_article_id,
            "title": "helpful",
            "category": CategoryEnum.ECONOMY.value,
        }
    ]


def test_get_my_helpful_analyses_applies_order_and_pagination(client):
    db = TestingSessionLocal()
    try:
        user = create_user(db, "pagination-user")
        for index in range(3):
            create_analysis(db, user.id, f"article-{index}", UserResponseEnum.GOOD)
        authenticate(client, user.id)
    finally:
        db.close()

    first_page = client.get("/api/users/me/helpful-analyses?limit=2&offset=0")
    second_page = client.get("/api/users/me/helpful-analyses?limit=2&offset=2")

    assert [item["title"] for item in first_page.json()] == [
        "article-2",
        "article-1",
    ]
    assert [item["title"] for item in second_page.json()] == ["article-0"]


def test_get_my_helpful_analyses_returns_empty_list(client):
    db = TestingSessionLocal()
    try:
        user = create_user(db, "empty-user")
        authenticate(client, user.id)
    finally:
        db.close()

    response = client.get("/api/users/me/helpful-analyses")

    assert response.status_code == 200
    assert response.json() == []


def test_get_my_helpful_analyses_requires_login(client):
    response = client.get("/api/users/me/helpful-analyses")

    assert response.status_code == 401
