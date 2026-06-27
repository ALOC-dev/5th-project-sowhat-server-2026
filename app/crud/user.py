from app.models.user import User


def create_user(db, payload):
    new_user = User(**payload.model_dump())

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except Exception:
        db.rollback()
        raise


def get_user_by_id(db, user_id):
    return db.query(User).filter(User.id == user_id).first()


def update_user(db, user_id, payload):
    db_user = db.query(User).filter(User.id == user_id).first()

    if db_user is None:
        return None

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