from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.personal_analysis import PersonalAnalysis


def create_analysis(db: Session, payload: dict) -> PersonalAnalysis:
    analysis = PersonalAnalysis(**payload)

    try:
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        return analysis
    except Exception:
        db.rollback()
        raise


def get_analysis_by_article_and_user(
    db: Session, article_id: int, user_id: int
) -> PersonalAnalysis:
    return (
        db.query(PersonalAnalysis)
        .filter(
            PersonalAnalysis.article_id == article_id,
            PersonalAnalysis.user_id == user_id,
        )
        .first()
    )


def update_analysis(db: Session, id: int, payload: dict) -> PersonalAnalysis:
    current_analysis = (
        db.query(PersonalAnalysis).filter(PersonalAnalysis.id == id).first()
    )
    if current_analysis is None:
        return None

    for key, value in payload.items():
        setattr(current_analysis, key, value)

    try:
        db.commit()
        db.refresh(current_analysis)
        return current_analysis
    except Exception:
        db.rollback()
        raise


# 사용자가 조회한 기사 목록을 최근 조회 순으로 반환
# 목록에 필요한 title, category를 개인해설에 함께 저장해 두므로 article을 조인하지 않는다
# personal_analysis에는 조회 시각 컬럼이 없어 id 역순을 최근 순으로 대신 쓴다
def get_viewed_analyses(
    db: Session, user_id: int, limit: int, offset: int
) -> list[PersonalAnalysis]:
    stmt = (
        select(PersonalAnalysis)
        .where(PersonalAnalysis.user_id == user_id)
        .order_by(PersonalAnalysis.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return db.execute(stmt).scalars().all()
