from app.models.article import Article


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
    print(f"[DEBUG] create_articles 호출됨: {len(articles)}건")
    article_objects = [Article(**article) for article in articles]

    try:
        print("[DEBUG] commit 시작")
        db.add_all(article_objects)
        db.commit()
        print("[DEBUG] commit 성공")
        return article_objects
    except Exception as e:
        db.rollback()
        print(f"[DEBUG] commit 실패: {e}")
        raise


def get_all_articles(db):
    return db.query(Article).all()


def get_article_by_id(db, article_id):
    return (
        db.query(Article)
        .filter(Article.id == article_id)
        .first()
    )


def get_article_by_source_url(db, source_url):
    return (
        db.query(Article)
        .filter(Article.source_url == source_url)
        .first()
    )


def update_article_by_id(db, article_id, payload):
    article = (
        db.query(Article)
        .filter(Article.id == article_id)
        .first()
    )

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