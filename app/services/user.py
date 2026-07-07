from enum import Enum

from sqlalchemy.orm import Session

import app.crud.user as crud
from app.models.user import User
from app.schemas.user import UserCreateRequest, UserUpdateRequest
from app.exceptions.domain import UserNotFoundError, InvalidArgumentError
from app.services.llm_service import filter_user_extra_information

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


async def create_user(db: Session, payload: UserCreateRequest) -> User:
    _validate_create_user_payload(payload)

    create_data = payload.model_dump()

    # llm 호출하여 필터링/요약된 문장 생성
    filtered = await filter_user_extra_information(payload.extra_information)
    create_data.update({"extra_information_filtered": filtered})

    user = crud.create_user(db, create_data)
    return user


def get_user(db: Session, user_id: int) -> User:
    user = crud.get_user_by_id(db, user_id)
    if user is None:
        raise UserNotFoundError()
    return user


async def modify_user(db: Session, user_id: int, payload: UserUpdateRequest) -> User:
    _validate_create_user_payload(payload)

    update_data = payload.model_dump()  # dict 형태로 변환

    # 수정하는 정보에 extra_information이 존재할 경우 llm 호출하여 필터링/요약된 문장 생성
    if payload.extra_information is not None:
        filtered = await filter_user_extra_information(payload.extra_information)
        print("[FILTERED]", filtered)  # TODO: 프롬프트 테스트 끝나면 지우기
        update_data.update(
            {"extra_information_filtered": filtered}
        )  # dict에 필터링된 문장 추가

    user = crud.update_user(db, user_id, update_data)
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
