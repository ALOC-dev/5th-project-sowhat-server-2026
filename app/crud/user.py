from app.models.user import User
from sqlalchemy.orm import Session


def create_user(db: Session, payload):
    new_user = User(**payload.model_dump())

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except Exception:
        db.rollback()
        raise


def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


def update_user(db: Session, user_id: int, payload):
    db_user = db.query(User).filter(User.id == user_id).first()

    if db_user is None:
        return None

    if type(payload) is dict:
        update_data = payload
    else:
        update_data = payload.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_user, key, value)

    try:
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception:
        db.rollback()
        raise


# def update_user_behavior_tags(db: Session, user_id: int, keywords: list[str]):
#     db_user = db.query(User).filter(User.id == user_id).first()

#     if db_user is None:
#         return None

#     current_interests = dict(db_user.behavior_interests or {})

#     for keyword in keywords:
#         if keyword:
#             current_interests[keyword] = current_interests.get(keyword, 0) + 1

#     db_user.behavior_interests = current_interests

#     try:
#         db.commit()
#         db.refresh(db_user)
#         return db_user
#     except Exception:
#         db.rollback()
#         raise
