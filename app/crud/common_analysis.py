MOCK_ANALYSES = [
    {
        "common_analysis_id": 1,
        "article_id": 1,
        "summary": "아 그때 살걸",
        "keyword": "개미: 소액 개인 투자자를 일컫는 은어.",
    },
    {
        "common_analysis_id": 2,
        "article_id": 2,
        "summary": "무슨 색깔 좋아해? 금지",
        "keyword": "선거: 공직을 맡을 개인이나 여러 사람을 선택하는 공식적인 집단 의사결정 과정.",
    },
    {
        "common_analysis_id": 3,
        "article_id": 3,
        "summary": "아 술자리 기빨린다",
        "keyword": "집돌이/집순이: 맨날 집에 가고 싶은 사람들. 컴과에 많이 분포한다",
    },
]


def get_analysis_by_article(article_id):
    for a in MOCK_ANALYSES:
        if a["article_id"] == article_id:
            return {"summary": a["summary"], "keyword": a["keyword"]}
    return None
