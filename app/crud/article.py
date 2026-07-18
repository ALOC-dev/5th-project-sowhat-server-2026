from datetime import datetime

from sqlalchemy.orm import Session
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from app.models.article import Article
from sqlalchemy import exists, select


def create_article(db: Session, payload: dict) -> Article:
    article = Article(**payload)
    try:
        db.add(article)
        db.commit()
        db.refresh(article)
        return article
    except Exception:
        db.rollback()
        raise


def create_articles(db: Session, articles: list[dict]) -> list[Article]:
    article_objects = [Article(**article) for article in articles]
    try:
        db.add_all(article_objects)
        db.commit()
        return article_objects
    except Exception as e:
        db.rollback()
        raise


# 최신 기사 최대 30개 불러오기 (overfetching 예방)
def get_all_articles(db: Session) -> list[Article]:
    stmt = select(Article).order_by(Article.published_at.desc()).limit(30)
    return db.execute(stmt).scalars().all()


# 나중에 페이지네이션 구현에 사용
# def get_all_articles(db, limit, offset):
#     stmt = (
#         select(Article)
#         .order_by(Article.published_at.desc())
#         .limit(limit)
#         .offset(offset)
#     )
#     return db.execute(stmt).scalars().all()


def get_articles_by_date(db: Session, date: datetime) -> list[Article]:
    return db.query(Article).filter(Article.published_at >= date).all()


def find_similar_articles(
    db: Session,
    date: datetime,
    user_embedding: list[float],
    top_k: int,
) -> list[Article]:
    stmt = (
        select(Article)
        .where(Article.published_at >= date)
        .order_by(Article.embedding.cosine_distance(user_embedding))
        .limit(top_k)
    )
    return db.execute(stmt).scalars().all()


def get_article_by_id(db: Session, article_id: int) -> Article:
    return db.query(Article).filter(Article.id == article_id).first()


def get_article_by_source_url(db: Session, source_url: str) -> Article:
    return db.query(Article).filter(Article.source_url == source_url).first()


def exists_similar_article(
    db: Session,
    date: datetime,
    article_embedding: list[float],
    threshold: float = 0.05,
) -> float:
    stmt = select(
        exists().where(
            (Article.published_at >= date)
            & (Article.embedding.cosine_distance(article_embedding) <= threshold)
        )
    )
    return db.execute(stmt).scalar()


def test_exists_similar_article(
    db: Session,
    date: datetime,
    article_embedding: list[float],
    threshold: float = 0.05,
) -> float:
    stmt = select(
        exists().where(
            (Article.published_at >= date)
            & (Article.embedding.cosine_distance(article_embedding) <= threshold)
        )
    )

    # return db.execute(stmt).scalar()

    # Test
    result = db.execute(stmt).scalar()

    stmt2 = (
        select(Article)
        .where(Article.published_at >= date)
        .order_by(Article.embedding.cosine_distance(article_embedding))
        .limit(1)
    )
    most_similar = db.execute(stmt2).scalars().first()
    if most_similar is not None:
        similarity = cosine_similarity(
            np.array(article_embedding).reshape(1, -1),
            np.array(most_similar.embedding).reshape(1, -1),
        )
    else:
        similarity = 0

    return result, similarity


def update_article_by_id(db: Session, article_id: int, payload: dict) -> Article:
    article = db.query(Article).filter(Article.id == article_id).first()

    if article is None:
        return None

    for key, value in payload.items():
        setattr(article, key, value)

    try:
        db.commit()
        db.refresh(article)
        return article
    except Exception:
        db.rollback()
        raise
