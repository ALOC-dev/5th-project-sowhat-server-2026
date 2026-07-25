from enum import Enum


class GenderEnum(str, Enum):
    MALE = "남"
    FEMALE = "여"


class RegionEnum(str, Enum):
    SEOUL = "서울"
    BUSAN = "부산"
    DAEGU = "대구"
    INCHEON = "인천"
    DAEJEON = "대전"
    ULSAN = "울산"
    GYEONGGI = "경기"
    GANGWON = "강원"
    CHUNGBUK = "충북"
    CHUNGNAM = "충남"
    JEONBUK = "전북"
    JEONNAM = "전남"
    GYEONGBUK = "경북"
    GYEONGNAM = "경남"
    JEJU = "제주"


class JobEnum(str, Enum):
    MANAGEMENT_BUSINESS = "경영·사업"
    FINANCE_INVESTMENT = "금융·투자"
    ACCOUNTING_TAX = "회계·세무"
    LAW_LEGAL = "법률·사법"
    PUBLIC_ADMINISTRATION = "공공·행정"
    POLITICS_DIPLOMACY = "정치·외교"
    EDUCATION = "교육"
    SCIENCE_RESEARCH = "과학·연구"
    IT_SOFTWARE = "IT·소프트웨어"
    DATA_AI = "데이터·AI"
    ENGINEERING_TECHNICAL = "공학·기술"
    MEDICAL_HEALTHCARE = "의료·보건"
    SOCIAL_WELFARE = "사회복지·상담"
    MEDIA_JOURNALISM = "언론·미디어"
    CULTURE_ARTS = "문화·예술"
    CONTENT_ENTERTAINMENT = "콘텐츠·엔터테인먼트"
    DESIGN_MARKETING = "디자인·광고·마케팅"
    CONSTRUCTION_ARCHITECTURE = "건설·건축"
    MANUFACTURING_PRODUCTION = "제조·생산"
    SALES_RETAIL = "판매·유통·영업"
    TRANSPORT_LOGISTICS = "운송·물류"
    AGRICULTURE_FISHERIES = "농림·축산·어업"
    SERVICE_TOURISM = "서비스·관광·외식"
    SPORTS = "스포츠·체육"
    PUBLIC_SAFETY = "군인·소방·경찰"
    STUDENT = "학생"
    JOB_SEEKER = "취업준비생"
    HOMEMAKER = "주부·가사"
    RETIRED_UNEMPLOYED = "은퇴·무직"


class CategoryEnum(str, Enum):
    POLITICS = "정치"
    ECONOMY = "경제"
    SOCIETY = "사회"
    INDUSTRY_IT = "산업/IT"


class PurposeEnum(str, Enum):
    GENERAL = "일반"
    STUDY = "공부"
    EMPLOYMENT_STARTUP = "취·창업"
    INVESTMENT = "투자"
