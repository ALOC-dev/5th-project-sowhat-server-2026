# from app.models.user_info import UserInfo

# from app.models.enums import GenderEnum, RegionEnum, JobEnum, CategoryEnum

MOCK_USERS = [
    {
        "user_id": 1,
        "age": 20,
        "gender": "MALE",
        "region": "SEOUL",
        "job": "STUDENT",
        "interest": "ECONOMY",
        "news_purpose": "EMPLOYMENT",
    },
    {
        "user_id": 2,
        "age": 25,
        "gender": "FEMALE",
        "region": "INCHEON",
        "job": "OFFICE_WORKER",
        "interest": "POLITICS",
        "news_purpose": "INVESTMENT",
    },
]


def create_user(db, payload):
    next_id = max((u["user_id"] for u in MOCK_USERS), default=0) + 1
    user_data = payload.model_dump()
    user_data["user_id"] = next_id
    MOCK_USERS.append(user_data)
    return user_data

    # new_user = UserInfo(**payload.model_dump())
    # db.add(new_user)
    # db.commit()
    # db.refresh(new_user)
    # return new_user


def get_user_by_id(db, user_id):
    for u in MOCK_USERS:
        if u["user_id"] == user_id:
            return u
    return None

    # db_user = db.query(UserInfo).filter(UserInfo.user_id == user_id).first()

    # if not db_user:
    #     return None
    # return db_user


def update_user(db, user_id, payload):
    update_data = payload.model_dump(exclude_unset=True)

    for index, u in enumerate(MOCK_USERS):
        if u["user_id"] == user_id:

            MOCK_USERS[index].update(update_data)

            return MOCK_USERS[index]
        
    return None

    # db_user = db.query(UserInfo).filter(UserInfo.user_id == user_id).first()
    # if not db_user:
    #     return None

    # update_data = payload.model_dump(exclude_unset=True)

    # for key, value in update_data.items():
    #     setattr(db_user, key, value)

    # db.commit()
    # db.refresh(db_user)
    # return db_user
