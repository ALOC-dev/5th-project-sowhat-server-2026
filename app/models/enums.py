from enum import Enum


class GenderEnum(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"


class RegionEnum(str, Enum):
    SEOUL = "SEOUL"
    BUSAN = "BUSAN"
    DAEGU = "DAEGU"
    INCHEON = "INCHEON"
    DAEJEON = "DAEJEON"


class JobEnum(str, Enum):
    STUDENT = "STUDENT"
    OFFICE_WORKER = "OFFICE_WORKER"
    DEVELOPER = "DEVELOPER"
    JOB_SEEKER = "JOB_SEEKER"
    ETC = "ETC"


class CategoryEnum(str, Enum):
    POLITICS = "POLITICS"
    ECONOMY = "ECONOMY"
    SOCIETY = "SOCIETY"
    INDUSTRY_IT = "INDUSTRY_IT"


class PurposeEnum(str, Enum):
    EMPLOYMENT = "EMPLOYMENT"
    INVESTMENT = "INVESTMENT"
    POLICY = "POLICY"
    INDUSTRY = "INDUSTRY"
    SOCIAL = "SOCIAL"
    STUDY = "STUDY"
    STARTUP = "STARTUP"
    TECH = "TECH"
    GENERAL = "GENERAL"
