from sqlalchemy import exists, select

from app.models.user import User
from sqlalchemy.orm import Session


def create_user(db: Session, payload: dict) -> User:
    new_user = User(**payload)
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except Exception:
        db.rollback()
        raise


def get_user_by_id(db: Session, id: int) -> User:
    return db.query(User).filter(User.id == id).first()


def get_user_by_login_id(db: Session, login_id: str) -> User:
    return db.query(User).filter(User.login_id == login_id).first()


def exists_user_by_login_id(db: Session, login_id: str) -> bool:
    stmt = select(exists().where(User.login_id == login_id))
    return db.execute(stmt).scalar()


def update_user(db: Session, id: int, payload: dict) -> User:
    db_user = db.query(User).filter(User.id == id).first()

    if db_user is None:
        return None

    for key, value in payload.items():
        setattr(db_user, key, value)

    try:
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception:
        db.rollback()
        raise


def delete_user_by_id(db: Session, id: int) -> bool:
    db_user = db.query(User).filter(User.id == id).first()

    if db_user is None:
        return False

    try:
        db.delete(db_user)
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise
