from sqlalchemy import Column, DateTime, Enum, Integer, Text, func
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
    age = Column(Integer, nullable=False)
    gender = Column(Enum(GenderEnum, name="gender_enum"), nullable=True)
    region = Column(Enum(RegionEnum, name="region_enum"), nullable=True)
    job = Column(Enum(JobEnum, name="job_enum"), nullable=True)
    interest = Column(Enum(CategoryEnum, name="category_enum"), nullable=True)
    purpose = Column(Enum(PurposeEnum, name="purpose_enum"), nullable=True)
    extra_information = Column(Text, nullable=True)
    embedding = Column(Vector(1536), nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
