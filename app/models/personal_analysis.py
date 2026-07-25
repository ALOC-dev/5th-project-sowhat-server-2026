from sqlalchemy import Column, ForeignKey, Integer, String, Text, UniqueConstraint
from app.db.database import Base


class PersonalAnalysis(Base):
    __tablename__ = "personal_analysis"
    __table_args__ = (
        UniqueConstraint(
            "article_id", "user_id", name="uq_personal_analysis_article_user"
        ),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    article_id = Column(Integer, ForeignKey("article.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, index=True)
    effect = Column(Text, nullable=False)
    solution = Column(Text, nullable=False)
    # solution에서 안내한 공식 창구의 조회/신청 주소 (해당 창구가 없으면 빈 값)
    link_name = Column(String(255), nullable=True)
    link = Column(String(255), nullable=True)
