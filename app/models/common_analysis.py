from sqlalchemy import Column, ForeignKey, Integer, String, Text, UniqueConstraint
from app.db.database import Base


class CommonAnalysis(Base):
    __tablename__ = "common_analysis"
    __table_args__ = (
        UniqueConstraint("article_id", name="uq_common_analysis_article_id"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    article_id = Column(Integer, ForeignKey("article.id"), nullable=False, index=True)
    summary = Column(Text)
    keyword = Column(String(255))
