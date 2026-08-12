from sqlalchemy.orm import Session

from app.models.enums import AgeGroupEnum, CategoryEnum, JobEnum
from app.models.experience_analysis import ExperienceAnalysis


def get_experience_analysis(
    db: Session,
    article_id: int,
    age_group: AgeGroupEnum,
    job: JobEnum,
    interest: CategoryEnum,
) -> ExperienceAnalysis:
    return (
        db.query(ExperienceAnalysis)
        .filter(
            ExperienceAnalysis.article_id == article_id,
            ExperienceAnalysis.age_group == age_group,
            ExperienceAnalysis.job == job,
            ExperienceAnalysis.interest == interest,
        )
        .first()
    )


def create_experience_analysis(db: Session, payload: dict) -> ExperienceAnalysis:
    experience_analysis = ExperienceAnalysis(**payload)

    try:
        db.add(experience_analysis)
        db.commit()
        db.refresh(experience_analysis)
        return experience_analysis
    except Exception:
        db.rollback()
        raise
