MOCK_ANALYSES = []


def create_analysis(payload):
    next_id = max((a["common_analysis_id"] for a in MOCK_ANALYSES), default=0) + 1
    analysis_data = payload.copy()
    analysis_data["common_analysis_id"] = next_id
    MOCK_ANALYSES.append(analysis_data)
    return analysis_data


def get_analysis_by_article(article_id):
    for a in MOCK_ANALYSES:
        if a["article_id"] == article_id:
            return {"summary": a["summary"], "keyword": a["keyword"]}
    return None
