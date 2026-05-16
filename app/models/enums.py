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


class InterestEnum(str, Enum):
    POLITICS = "POLITICS"
    ECONOMY = "ECONOMY"
    SOCIETY = "SOCIETY"
