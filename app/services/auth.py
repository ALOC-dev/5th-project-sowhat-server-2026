# TODO:
#   로그인 로그아웃 구현 (민우오빠)

from sqlalchemy.orm import Session

import app.crud.user as crud
import app.services.user as user_service
from app.core.security import hash_password
from app.exceptions.domain import DuplicateEmailError
from app.models.user import User
from app.schemas.user import SignupRequest


async def signup(db: Session, payload: SignupRequest) -> User:
    user_service._validate_create_user_payload(payload)

    if crud.get_user_by_email(db, payload.email) is not None:
        raise DuplicateEmailError()

    user_data = payload.model_dump(exclude={"password"})
    user_data["hashed_password"] = hash_password(payload.password)

    user = crud.create_user(db, user_data)
    return await user_service.attach_profile_embedding(db, user)
