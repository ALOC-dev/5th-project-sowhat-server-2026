# 응답 이후 실행되는 임베딩 생성 백그라운드 태스크 모음
# 요청 세션은 백그라운드 실행 전에 닫히므로 각 태스크가 자체 세션을 연다
from datetime import datetime, timedelta

import numpy as np
from sqlalchemy.orm import Session

import app.crud.article as article_crud
import app.crud.user as user_crud
from app.db.database import SessionLocal
from app.models.article import Article
from app.services.llm_service import (
    generate_article_embedding,
    generate_user_profile_embedding,
)


# 기사 임베딩 반환, 없으면 생성해 저장
async def _get_or_create_article_embedding(db: Session, article: Article) -> None:
    if article.embedding is not None:
        return article.embedding

    embedding, summary = await generate_article_embedding(article)
    payload = {"embedding": embedding}
    if summary is not None:
        payload["summary"] = summary

    article_crud.update_article_by_id(db, article.id, payload)
    return embedding


# 기사 임베딩이 없으면 생성해 저장 (이미 있으면 스킵 → 중복 요청에도 멱등)
async def ensure_article_embedding(article_id: int) -> None:
    db = SessionLocal()
    try:
        article = article_crud.get_article_by_id(db, article_id)
        if article is not None:
            await _get_or_create_article_embedding(db, article)

        # 유사도 지나치게 높은 기사 필터링
        if article.embedding is not None and article_crud.exists_similar_article(
            db,
            datetime.now() - timedelta(hours=24),
            article.id,
            article.embedding,
            0.3,  # 유사도 기준 수정 필요
        ):
            article_crud.delete_article_by_id(db, article.id)
            print(f"[DELETE] 지나치게 유사한 기사 자동 삭제")

    except Exception as exc:
        print(
            f"[ERROR] 기사 임베딩 백그라운드 생성 실패 (article_id={article_id}): {exc}"
        )
    finally:
        db.close()


# 사용자가 클릭한 기사를 행동 임베딩에 반영 (기존 0.9 : 기사 0.1 가중합 후 정규화)
async def update_behavior_embedding(user_id: int, article_id: int) -> None:
    db = SessionLocal()
    try:
        user = user_crud.get_user_by_id(db, user_id)
        article = article_crud.get_article_by_id(db, article_id)
        if user is None or article is None:
            return

        # 행동 임베딩이 없으면 프로필 임베딩에서 시작, 그것도 없으면 새로 생성
        behavior_embedding = user.behavior_embedding
        if behavior_embedding is None:
            behavior_embedding = user.profile_embedding
        if behavior_embedding is None:
            behavior_embedding = await generate_user_profile_embedding(user)
            user_crud.update_user(
                db, user_id, {"profile_embedding": behavior_embedding}
            )

        article_embedding = await _get_or_create_article_embedding(db, article)

        behavior_embedding = behavior_embedding * 0.9 + article_embedding * 0.1
        behavior_embedding /= np.linalg.norm(behavior_embedding)  # 정규화
        user_crud.update_user(db, user_id, {"behavior_embedding": behavior_embedding})
    except Exception as exc:
        print(
            f"[ERROR] 행동 임베딩 백그라운드 업데이트 실패 "
            f"(user_id={user_id}, article_id={article_id}): {exc}"
        )
    finally:
        db.close()
