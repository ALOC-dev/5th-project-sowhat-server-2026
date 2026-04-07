from sqlalchemy import Column, ForeignKey, Integer, String, Text, UniqueConstraint
from app.db.database import Base




class CommonAnalysis(Base):
    __tablename__ = "common_analysis_id"
    __table_args__ = (
        UniqueConstraint("article_id", name="uq_common_analysis_article_id"),
    )

    analysis_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    article_id = Column(Integer, ForeignKey("article.article_id"), nullable=False, index=True)
    summary = Column(Text)
    keyword = Column(String(255))