import re
from enum import Enum

from sqlalchemy.orm import Session

import app.crud.user as crud
from app.models.user import User
from app.schemas.filtered_extra_information import FilteredExtraInformation
from app.schemas.user import UserCreateRequest, UserUpdateRequest
from app.exceptions.domain import UserNotFoundError, InvalidArgumentError
from app.services.llm_service import generate_user_profile_embedding
from app.services.llm_service import filter_user_extra_information

USER_ENUM_FIELD_NAMES = ("gender", "region", "job", "interest", "purpose")


def _validate_login_id(value, field_name: str = "사용자 ID") -> None:
    if value is None or not isinstance(value, str):
        raise InvalidArgumentError(f"{field_name}를 올바른 형식으로 입력해 주세요.")
    elif len(value) < 4 or not re.fullmatch(r"[A-Za-z0-9_]+", value):
        raise InvalidArgumentError(
            f"{field_name}는 4자 이상이며 영문 대소문자·숫자·언더바( _ ) 기호만 포함해야 해요."
        )


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


def _validate_create_user_payload(payload: UserCreateRequest) -> None:
    _validate_login_id(payload.login_id)

    _validate_natural_number(payload.age, "age")

    for field_name in USER_ENUM_FIELD_NAMES:
        enum_class = _get_payload_field_annotation(payload, field_name)
        if not isinstance(enum_class, type) or not issubclass(enum_class, Enum):
            continue

        _validate_enum_value(getattr(payload, field_name), enum_class, field_name)


def _validate_update_user_payload(payload: UserUpdateRequest) -> None:
    if payload.age:
        _validate_natural_number(payload.age, "age")

    for field_name in USER_ENUM_FIELD_NAMES:
        enum_class = _get_payload_field_annotation(payload, field_name)
        if not isinstance(enum_class, type) or not issubclass(enum_class, Enum):
            continue

        _validate_enum_value(getattr(payload, field_name), enum_class, field_name)


def _validate_user_extra_information(payload: FilteredExtraInformation) -> str:
    if not payload.success:
        raise InvalidArgumentError(
            "사용자 입력란에는 개인정보 및 위험한 정보(범죄, 폭력, 혐오 발언 등)를 작성할 수 없습니다."
        )
    return payload.summary


# 가입 시점에 프로필 임베딩 생성
# 실패해도 가입은 유지 (임베딩은 추천 시 lazy 생성되는 fallback 존재)
async def attach_profile_embedding(db: Session, user: User) -> User:
    try:
        profile_embedding = await generate_user_profile_embedding(user)
        user = crud.update_user(db, user.id, {"profile_embedding": profile_embedding})
    except Exception as e:
        print(f"프로필 임베딩 생성 실패 (user_id={user.id}): {e}")

    return user


async def create_user(
    db: Session, payload: UserCreateRequest, background_tasks
) -> User:
    _validate_create_user_payload(payload)
    # user = crud.create_user(db, payload.model_dump())

    create_data = payload.model_dump()

    # llm 호출하여 필터링/요약된 문장 생성
    filtered = await filter_user_extra_information(payload.extra_information)
    summary = _validate_user_extra_information(filtered)
    create_data.update(
        {
            "extra_information": payload.extra_information,
            "filtered_extra_information": summary,
        }
    )  # dict에 원본 문장, 필터링된 문장 추가

    user = crud.create_user(db, create_data)
    # 프로필 임베딩 생성은 백그라운드로 빼기
    background_tasks.add_task(attach_profile_embedding, db, user)

    return user


def get_user(db: Session, user_id: int) -> User:
    user = crud.get_user_by_id(db, user_id)
    if user is None:
        raise UserNotFoundError()
    return user


async def update_user(
    db: Session, user_id: int, payload: UserUpdateRequest, background_tasks
) -> User:
    _validate_update_user_payload(payload)

    update_data = payload.model_dump(exclude_unset=True)  # dict 형태로 변환

    # 수정하는 정보에 extra_information이 존재할 경우 llm 호출하여 필터링/요약된 문장 생성
    if payload.extra_information is not None:
        filtered = await filter_user_extra_information(payload.extra_information)
        summary = _validate_user_extra_information(filtered)
        update_data.update(
            {
                "extra_information": payload.extra_information,
                "filtered_extra_information": summary,
            }
        )  # dict에 원본 문장, 필터링된 문장 추가

    user = crud.update_user(db, user_id, update_data)
    if user is None:
        raise UserNotFoundError()

    # 프로필 임베딩 생성은 백그라운드로 빼기
    background_tasks.add_task(attach_profile_embedding, db, user)
    return user


def check_duplicate_id(db: Session, payload: dict[str, str]) -> dict[str, bool]:
    login_id = payload.get("login_id", None)
    _validate_login_id(login_id)

    exists = crud.exists_user_by_login_id(db, login_id)
    return {"available": not exists}
