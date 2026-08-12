from sqlalchemy import Column, Enum, ForeignKey, Integer, Text, UniqueConstraint

from app.db.database import Base
from app.models.enums import AgeGroupEnum, CategoryEnum, JobEnum


# 비로그인 사용자용 라이트 개인해설 캐시 (기사 x 연령대 x 직업 x 관심사 조합별로 재활용)
class ExperienceAnalysis(Base):
    __tablename__ = "experience_analysis"
    __table_args__ = (
        UniqueConstraint(
            "article_id",
            "age_group",
            "job",
            "interest",
            name="uq_experience_analysis_key",
        ),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    article_id = Column(
        Integer,
        ForeignKey("article.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    age_group = Column(Enum(AgeGroupEnum, name="age_group_enum"), nullable=False)
    job = Column(Enum(JobEnum, name="job_enum"), nullable=False)
    interest = Column(Enum(CategoryEnum, name="category_enum"), nullable=False)
    effect = Column(Text, nullable=False)
