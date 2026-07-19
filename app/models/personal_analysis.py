from sqlalchemy import Column, ForeignKey, Integer, Text, UniqueConstraint
from app.db.database import Base


class PersonalAnalysis(Base):
    __tablename__ = "personal_analysis"
    __table_args__ = (
        UniqueConstraint(
            "article_id", "user_id", name="uq_personal_analysis_article_user"
        ),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    article_id = Column(
        Integer,
        ForeignKey("article.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        Integer,
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    effect = Column(Text, nullable=False)
    solution = Column(Text, nullable=False)
