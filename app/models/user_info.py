from sqlalchemy import Column, Enum, Integer
from app.db.database import Base

from app.models.enums import GenderEnum, RegionEnum, JobEnum, CategoryEnum


class UserInfo(Base):
    __tablename__ = "user_info"

    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    age = Column(Integer, nullable=False)
    gender = Column(Enum(GenderEnum, name="gender_enum"), nullable=False)
    region = Column(Enum(RegionEnum, name="region_enum"), nullable=False)
    job = Column(Enum(JobEnum, name="job_enum"), nullable=False)
    interest = Column(Enum(CategoryEnum, name="category_enum"), nullable=False)
