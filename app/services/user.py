from enum import Enum

from sqlalchemy.orm import Session

import app.crud.user as crud
from app.models.user import User
from app.schemas.user import UserCreateRequest, UserUpdateRequest
from app.exceptions.domain import UserNotFoundError, InvalidArgumentError
from app.services.llm_service import generate_user_profile_embedding

USER_ENUM_FIELD_NAMES = ("gender", "region", "job", "interest", "purpose")


def _validate_natural_number(value, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise InvalidArgumentError(f"{field_name}은(는) 자연수여야 합니다.")


def _validate_enum_value(value, enum_class: type[Enum], field_name: str) -> None:
    if isinstance(value, enum_class):
        return

    if isinstance(value, str) and value in {item.value for item in enum_class}:
        return

    allowed_values = ", ".join(item.value for item in enum_class)
    raise InvalidArgumentError(
        f"{field_name}은(는) 다음 값 중 하나여야 합니다: {allowed_values}"
    )


def _get_payload_field_annotation(
    payload: UserCreateRequest | UserUpdateRequest, field_name: str
):
    model_fields = getattr(payload.__class__, "model_fields", {})
    field = model_fields.get(field_name)
    return getattr(field, "annotation", None)


def _validate_create_user_payload(
    payload: UserCreateRequest | UserUpdateRequest,
) -> None:
    _validate_natural_number(payload.age, "age")

    for field_name in USER_ENUM_FIELD_NAMES:
        enum_class = _get_payload_field_annotation(payload, field_name)
        if not isinstance(enum_class, type) or not issubclass(enum_class, Enum):
            continue

        _validate_enum_value(getattr(payload, field_name), enum_class, field_name)


# 가입 시점에 프로필 임베딩 생성
# 실패해도 가입은 유지 (임베딩은 추천 시 lazy 생성되는 fallback 존재)
async def attach_profile_embedding(db: Session, user: User) -> User:
    try:
        profile_embedding = await generate_user_profile_embedding(user)
        user = crud.update_user(db, user.id, {"profile_embedding": profile_embedding})
    except Exception as e:
        print(f"프로필 임베딩 생성 실패 (user_id={user.id}): {e}")

    return user


async def create_user(db: Session, payload: UserCreateRequest) -> User:
    _validate_create_user_payload(payload)
    user = crud.create_user(db, payload.model_dump())
    return await attach_profile_embedding(db, user)


def get_user(db: Session, user_id: int) -> User:
    user = crud.get_user_by_id(db, user_id)
    if user is None:
        raise UserNotFoundError()
    return user


def modify_user(db: Session, user_id: int, payload: UserUpdateRequest) -> User:
    _validate_create_user_payload(payload)
    user = crud.update_user(db, user_id, payload.model_dump())
    if user is None:
        raise UserNotFoundError()
    return user


# def update_user_interests(db: Session, user_id: int, article_id: int) -> User:

#     user = get_user(db, user_id)

#     import app.crud.article as article_crud

#     article = article_crud.get_article_by_id(db, article_id)
#     if article is None or not article.keyword:
#         return user

#     keywords = (
#         [k.strip() for k in article.keyword.split(",")]
#         if isinstance(article.keyword, str)
#         else article.keyword
#     )

#     updated_user = crud.update_user_behavior_tags(db, user_id, keywords)
#     return updated_user
