from sqlalchemy import Column, DateTime, Enum, Integer, Text, func, JSON
from pgvector.sqlalchemy import Vector
from app.db.database import Base

from app.models.enums import (
    GenderEnum,
    RegionEnum,
    JobEnum,
    CategoryEnum,
    PurposeEnum,
)


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # 인증 도입 이전에 생성된 유저는 email/hashed_password가 없으므로 nullable
    email = Column(Text, unique=True, index=True, nullable=True)
    hashed_password = Column(Text, nullable=True)
    age = Column(Integer, nullable=False)
    gender = Column(Enum(GenderEnum, name="gender_enum"), nullable=True)
    region = Column(Enum(RegionEnum, name="region_enum"), nullable=True)
    job = Column(Enum(JobEnum, name="job_enum"), nullable=True)
    interest = Column(Enum(CategoryEnum, name="category_enum"), nullable=True)
    purpose = Column(Enum(PurposeEnum, name="purpose_enum"), nullable=True)
    extra_information = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    behavior_interests = Column(JSON, default=dict, nullable=True)
    profile_embedding = Column(Vector(1536), nullable=True)
    behavior_embedding = Column(Vector(1536), nullable=True)
