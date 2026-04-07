MOCK_ANALYSES = [
    {
        "personal_analysis_id": 1,
        "article_id": 1,
        "user_id": 1,
        "effect": "이 소식은 이런 영향을 줄 수 있어요",
        "solution": "이렇게 대비하면 좋아요",
    },
    {
        "personal_analysis_id": 2,
        "article_id": 1,
        "user_id": 2,
        "effect": "이 소식은 이런 영향을 줄 수 있어요",
        "solution": "이렇게 대비하면 좋아요",
    },
    {
        "personal_analysis_id": 3,
        "article_id": 2,
        "user_id": 1,
        "effect": "이 소식은 이런 영향을 줄 수 있어요",
        "solution": "이렇게 대비하면 좋아요",
    },
    {
        "personal_analysis_id": 4,
        "article_id": 2,
        "user_id": 2,
        "effect": "이 소식은 이런 영향을 줄 수 있어요",
        "solution": "이렇게 대비하면 좋아요",
    },
]


def get_analysis_by_article_and_user(article_id, user_id):
    for a in MOCK_ANALYSES:
        if a["article_id"] == article_id and a["user_id"] == user_id:
            return {"effect": a["effect"], "solution": a["solution"]}
