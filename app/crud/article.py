# 시작할 때는 비어있는 리스트 준비, 기사 크롤링 후 저장하기
MOCK_ARTICLES = []


def create_article(payload):
    next_id = max((a["id"] for a in MOCK_ARTICLES), default=0) + 1
    new_article = payload.model_dump()
    new_article["id"] = next_id
    new_article["category"] = "미분류"  # 임시
    MOCK_ARTICLES.append(new_article)
    return new_article


def create_articles(articles):
    for article in articles:
        create_article(article)


def get_all_articles():
    return MOCK_ARTICLES


def get_article_by_id(id):
    for a in MOCK_ARTICLES:
        if a["id"] == id:
            return a

    return None
