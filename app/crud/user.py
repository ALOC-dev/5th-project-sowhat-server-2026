from app.models.user_info import GenderEnum, RegionEnum, JobEnum, InterestEnum

MOCK_USERS = [
    {
        "user_id": 1,
        "age": 20,
        "gender": GenderEnum.MALE,
        "region": RegionEnum.SEOUL,
        "job": JobEnum.STUDENT,
        "interest": InterestEnum.ECONOMY,
    },
    {
        "user_id": 2,
        "age": 25,
        "gender": GenderEnum.FEMALE,
        "region": RegionEnum.INCHEON,
        "job": JobEnum.OFFICE_WORKER,
        "interest": InterestEnum.POLITICS,
    },
]


def create_user(payload):
    MOCK_USERS.append(payload)
    return True


def get_user_by_id(user_id):
    for u in MOCK_USERS:
        if u["user_id"] == user_id:
            return u

    return None
