# 시작할 때는 비어있는 리스트 준비, 기사 크롤링->LLM 호출 후 저장하기
MOCK_ANALYSES = []


def create_analysis(payload):
    next_id = max((a["personal_analysis_id"] for a in MOCK_ANALYSES), default=0) + 1
    analysis_data = payload.copy()
    analysis_data["personal_analysis_id"] = next_id
    MOCK_ANALYSES.append(analysis_data)
    return analysis_data


def get_analysis_by_article_and_user(article_id, user_id):
    for a in MOCK_ANALYSES:
        if a["article_id"] == article_id and a["user_id"] == user_id:
            return {"effect": a["effect"], "solution": a["solution"]}
    return None
