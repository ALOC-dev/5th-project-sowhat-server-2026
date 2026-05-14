# MOCK_ARTICLES = [
#     {
#         "article_id": 1,
#         "title": "경제뉴스",
#         "date": "2026-04-03 10:00:00",
#         "content": "최근 국내 증시 변동성이 확대되면서 개인 투자자들의 관심이 다시 높아지고 있다. 코스피와 코스닥 시장에서는 업종별 주가 흐름이 크게 엇갈리는 모습이 나타났고, 일부 종목에는 매수세가 집중됐다. 증권가는 미국 금리 정책과 글로벌 경기 둔화 가능성 등 대외 변수로 인해 시장 불확실성이 당분간 이어질 수 있다고 보고 있다. 이에 따라 투자자들 사이에서는 종목 선택과 매수 시점을 두고 신중한 접근이 필요하다는 의견이 나오고 있다. 일각에서는 단기 변동성에 흔들리기보다 기업 실적과 산업 전망을 함께 살펴야 한다는 조언도 제기된다.",
#         "category": "ECONOMY",
#     },
#     {
#         "article_id": 2,
#         "title": "정치뉴스",
#         "date": "2026-04-03 11:00:00",
#         "content": "정치뉴스입니다. 술 먹을때 정치얘기하지 맙시다.",
#         "category": "POLITICS",
#     },
#     {
#         "article_id": 3,
#         "title": "사회뉴스",
#         "date": "2026-04-03 12:00:00",
#         "content": "사회뉴스입니다. 사회에 관심이 없습니다.",
#         "category": "SOCIETY",
#     },
# ]

# 시작할 때는 비어있는 리스트 준비, 기사 크롤링 후 저장하기
MOCK_ARTICLES = []


def create_article(payload):
    next_id = max((a["article_id"] for a in MOCK_ARTICLES), default=0) + 1
    article_data = payload.copy()
    article_data["article_id"] = next_id
    MOCK_ARTICLES.append(article_data)
    return article_data


def get_all_articles():
    return MOCK_ARTICLES


def get_article_by_id(id):
    for a in MOCK_ARTICLES:
        if a["article_id"] == id:
            return a

    return None
