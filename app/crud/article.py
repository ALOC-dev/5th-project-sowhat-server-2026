from app.models.article import Article
from sqlalchemy import select


def create_article(db, payload):
    article = Article(**payload)

    try:
        db.add(article)
        db.commit()
        db.refresh(article)
        return article
    except Exception:
        db.rollback()
        raise


def create_articles(db, articles):
    article_objects = [Article(**article) for article in articles]

    try:
        db.add_all(article_objects)
        db.commit()
        return article_objects
    except Exception as e:
        db.rollback()
        raise


# 최신 기사 최대 30개 불러오기 (overfetching 예방)
def get_all_articles(db):
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


def get_articles_by_date(db, date):
    return db.query(Article).filter(Article.published_at >= date).all()


def get_articles_by_cosine_similarity(db, date, user_embedding, limit):
    stmt = (
        select(Article)
        .where(Article.published_at >= date)
        .order_by(Article.embedding.cosine_distance(user_embedding))
        .limit(limit)
    )
    return db.execute(stmt).scalars().all()


def get_article_by_id(db, article_id):
    return db.query(Article).filter(Article.id == article_id).first()


def get_article_by_source_url(db, source_url):
    return db.query(Article).filter(Article.source_url == source_url).first()


def update_article_by_id(db, article_id, payload):
    article = db.query(Article).filter(Article.id == article_id).first()

    if article is None:
        return None

    if type(payload) is dict:
        update_data = payload
    else:
        update_data = payload.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(article, key, value)

    try:
        db.commit()
        db.refresh(article)
        return article
    except Exception:
        db.rollback()
        raise
