from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, Enum as SqlEnum, Integer, String, Text
from sqlalchemy.sql import func
from app.db.database import Base


class CategoryEnum(PyEnum):
    POLITICS = "POLITICS"
    ECONOMY = "ECONOMY"
    SOCIETY = "SOCIETY"


class Article(Base):
    __tablename__ = "article"

    article_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    content_preview = Column(Text, nullable=False)
    category = Column(SqlEnum(CategoryEnum, name="category_enum"), nullable=False)