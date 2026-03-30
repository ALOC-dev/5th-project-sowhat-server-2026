from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from pydantic import BaseModel  # 요청 body 검증(region, intersts 등)
from typing import List

app = FastAPI()  # 앱 생성


# DB 연결 테스트
@app.get("/")
def read_root(db: Session = Depends(get_db)):
    return {"message": "Neon DB connected"}


# 임시 데이터(DB가 없기때문에 임시로 생성)
profiles = []  # 사용자 프로필
articles = [  # 기사
    {
        "id": 1,
        "title": "객체지향프로그래밍및실습",
        "category": "전공선택",
        "region": "seoul",
        "age_group": "2학년",
        "summary": "저번 주 휴강이라 좋았는데...",
        "original_url": "https://example.com/article1",
    },
    {
        "id": 2,
        "title": "자료구조",
        "category": "전공필수",
        "region": "seoul",
        "age_group": "2학년",
        "summary": "머리가 너무 아픔",
        "original_url": "https://example.com/article2",
    },
    {
        "id": 3,
        "title": "컴퓨터과학개론",
        "category": "전공선택",
        "region": "busan",
        "age_group": "1학년",
        "summary": "1학년 하고싶다",
        "original_url": "https://example.com/article3",
    },
]

analyses = {}  # 기사 해설 결과를 저장


# Pydantic 모델: 프로필 생성 요청 형식
class ProfileCreate(BaseModel):
    region: str
    interests: List[str]
    age_group: str


# # 기본 확인
# @app.get("/")
# def root():
#     return {"message": "FastAPI server is running"}  # 브라우저에서 /로 들어오면 출력


@app.get("/health")
def health():
    return {"status": "ok"}  # 서버 정상 동작 여부 확인용


# 프로필
@app.post("/profiles")
def create_profile(profile: ProfileCreate):
    new_profile = {
        "id": len(profiles) + 1,
        "region": profile.region,
        "interests": profile.interests,
        "age_group": profile.age_group,
    }
    profiles.append(new_profile)
    return {"message": "profile created", "data": new_profile}


@app.get("/profiles")
def get_profiles():
    return profiles


# 기사 목록 조회
@app.get("/articles")
def get_articles(category: str | None = None, region: str | None = None):
    result = articles

    if category:
        result = [a for a in result if a["category"] == category]

    if region:
        result = [a for a in result if a["region"] == region]

    return result


# 기사 상세 조회
@app.get("/articles/{article_id}")
def get_article(article_id: int):
    article = next((a for a in articles if a["id"] == article_id), None)

    if not article:
        raise HTTPException(status_code=404, detail="article not found")

    return article


# 기사 해설 (목데이터)
@app.post("/articles/{article_id}/analyze")
def analyze_article(article_id: int):
    article = next((a for a in articles if a["id"] == article_id), None)

    if not article:
        raise HTTPException(status_code=404, detail="article not found")

    if article_id in analyses:
        return {"message": "cached analysis returned", "data": analyses[article_id]}

    analysis_result = {
        "article_id": article_id,
        "easy_summary": f"{article['title']}에 대한 쉬운 요약입니다.",
        "terms": [
            {"term": "교수님", "description": "열심히 하십니다"},
            {"term": "수업", "description": "구체적으로 설명해주십니다"},
        ],
        "personal_impact": "수업을 잘 들어야 학점을 잘 받습니다",
        "action_guide": ["공부 열심히 해야됩니다.", "수업시간에 집중해야합니다"],
        "official_links": [{"title": "타이틀", "url": "https://www.gov.kr"}],
    }

    analyses[article_id] = analysis_result

    return {"message": "analysis created", "data": analysis_result}


# 이미 저장된 해설 출력
@app.get("/articles/{article_id}/analysis")
def get_article_analysis(article_id: int):
    if article_id not in analyses:
        raise HTTPException(status_code=404, detail="analysis not found")

    return analyses[article_id]
