from app.crud.articles import get_all_articles


def list_articles():
    articles = get_all_articles()

    result = []

    for article in articles:
        preview = article["content"][:25]
        if len(article["content"]) > 25:
            preview += "..."

        result.append(
            {
                "article_id": article["article_id"],
                "title": article["title"],
                "date": article["date"],
                "content_preview": preview,
                "category": article["category"],
            }
        )

    return result