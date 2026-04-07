MOCK_ARTICLES = [
    {
        "article_id": 1,
        "title": "경제뉴스",
        "date": "2026-04-03 10:00:00",
        "content": "경제뉴스입니다. 요새 주식하는 친구들이 너무 시끄럽습니다.",
        "category": "ECONOMY",
    },
    {
        "article_id": 2,
        "title": "정치뉴스",
        "date": "2026-04-03 11:00:00",
        "content": "정치뉴스입니다. 술 먹을때 정치얘기하지 맙시다.",
        "category": "POLITICS",
    },
    {
        "article_id": 3,
        "title": "사회뉴스",
        "date": "2026-04-03 12:00:00",
        "content": "사회뉴스입니다. 사회에 관심이 없습니다.",
        "category": "SOCIETY",
    },
]


def get_all_articles():
    return MOCK_ARTICLES


def get_article_by_id(id):
    for a in MOCK_ARTICLES:
        if a["article_id"] == id:
            return a

    return None
