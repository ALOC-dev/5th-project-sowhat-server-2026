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
