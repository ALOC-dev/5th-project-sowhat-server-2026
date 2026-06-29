from sqlalchemy import Column, DateTime, Enum, Integer, String, Text
from sqlalchemy.sql import func
from app.db.database import Base
from app.models.enums import CategoryEnum


class Article(Base):
    __tablename__ = "article"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    source_url = Column(String(255), nullable=False)
    published_at = Column(
        DateTime(timezone=True), nullable=False
    )
    publisher = Column(String(255), nullable=False)
    reporter = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    keyword = Column(String(255), nullable=True)
    category = Column(Enum(CategoryEnum, name="category", create_type=False), nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
