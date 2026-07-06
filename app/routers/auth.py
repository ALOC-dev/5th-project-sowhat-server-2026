from fastapi import APIRouter, Depends

import app.services.auth as service

router = APIRouter(prefix="/api/auth")

# TODO:
#   로그인 로그아웃 구현 (민우오빠)
#   회원가입 구현 (지원언니)


@router.post("/login")
def login():
    pass


@router.post("/logout")
def logout():
    pass


@router.post("/signup")
def signup():
    pass
