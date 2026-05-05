from app.models.user_info import GenderEnum, RegionEnum, JobEnum, InterestEnum

### 추후 DB 연결해서 대폭 수정 예정! ###

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
    next_id = max((u["user_id"] for u in MOCK_USERS), default=0) + 1
    user_data = payload.copy()
    user_data["user_id"] = next_id
    MOCK_USERS.append(user_data)
    return user_data


def get_user_by_id(user_id):
    for u in MOCK_USERS:
        if u["user_id"] == user_id:
            return u
    return None


def update_user(user_id, payload):
    for index, u in enumerate(MOCK_USERS):
        if u["user_id"] == user_id:
            updated = {
                "user_id": user_id,
                "age": payload["age"],
                "gender": payload["gender"],
                "region": payload["region"],
                "job": payload["job"],
                "interest": payload["interest"],
            }
            MOCK_USERS[index] = updated
            return updated
    return None
