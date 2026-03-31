from enum import Enum as PyEnum

from sqlalchemy import Column, Enum as SqlEnum, Integer
from app.db.database import Base


class GenderEnum(PyEnum):
    MALE = "MALE"
    FEMALE = "FEMALE"


class RegionEnum(PyEnum):
    SEOUL = "SEOUL"
    BUSAN = "BUSAN"
    DAEGU = "DAEGU"
    INCHEON = "INCHEON"
    DAEJEON = "DAEJEON"

class JobEnum(PyEnum):
    STUDENT = "STUDENT"
    OFFICE_WORKER = "OFFICE_WORKER"
    DEVELOPER = "DEVELOPER"
    JOB_SEEKER = "JOB_SEEKER"
    ETC = "ETC"


class InterestEnum(PyEnum):
    POLITICS = "POLITICS"
    ECONOMY = "ECONOMY"
    SOCIETY = "SOCIETY"


class UserInfo(Base):
    __tablename__ = "user_info"

    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    age = Column(Integer, nullable=False)
    gender = Column(SqlEnum(GenderEnum, name="gender_enum"), nullable=False)
    region = Column(SqlEnum(RegionEnum, name="region_enum"), nullable=False)
    job = Column(SqlEnum(JobEnum, name="job_enum"), nullable=False)
    interest = Column(SqlEnum(InterestEnum, name="interest_enum"), nullable=False)