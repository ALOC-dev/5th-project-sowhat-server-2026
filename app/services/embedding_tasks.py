# 응답 이후 실행되는 임베딩 생성 백그라운드 태스크 모음
# 요청 세션은 백그라운드 실행 전에 닫히므로 각 태스크가 자체 세션을 연다
from datetime import datetime, timedelta

import numpy as np
from sqlalchemy.orm import Session

import app.crud.article as article_crud
import app.crud.user as user_crud
from app.db.database import SessionLocal
from app.models.article import Article
from app.models.user import User
from app.services.llm_service import (
    generate_article_embedding,
    generate_user_profile_embedding,
)
from sklearn.metrics.pairwise import cosine_distances


# 기사 임베딩 반환, 없으면 생성해 저장
async def _get_or_create_article_embedding(
    db: Session, article: Article
) -> list[float]:
    if article.embedding is not None:
        return article.embedding

    embedding, common_analysis = await generate_article_embedding(article)

    article_crud.update_article_by_id(
        db, article.id, {"embedding": embedding, **common_analysis}
    )
    return embedding


# 사용자 프로필 & 행동 임베딩 반환, 없으면 생성해 저장
async def get_or_create_user_embedding(db: Session, user: User):
    payload = {}  # 변경사항 DB 저장을 위한 dict

    # 프로필 임베딩 불러오기 (없으면 생성)
    profile_embedding = user.profile_embedding
    if profile_embedding is None:
        profile_embedding = await generate_user_profile_embedding(user)
        payload["profile_embedding"] = profile_embedding

    # 행동 임베딩 불러오기 (없으면 프로필 임베딩 사용)
    behavior_embedding = user.behavior_embedding
    if behavior_embedding is None:
        behavior_embedding = profile_embedding
        payload["behavior_embedding"] = behavior_embedding

    if payload is not {}:
        user_crud.update_user(db, user.id, payload)
    return profile_embedding, behavior_embedding


# 기사 임베딩이 없으면 생성해 저장 (이미 있으면 스킵 → 중복 요청에도 멱등)
async def ensure_article_embedding(article_id: int) -> None:
    db = SessionLocal()
    try:
        article = article_crud.get_article_by_id(db, article_id)
        if article is not None:
            embedding = await _get_or_create_article_embedding(db, article)

        # 유사도 지나치게 높은 기사 필터링
        if embedding is not None and article_crud.exists_similar_article(
            db,
            datetime.now() - timedelta(hours=24),
            article.id,
            embedding,
            0.3,  # 유사도 기준 수정 필요
        ):
            article_crud.delete_article_by_id(db, article.id)
            print(f"[DELETE] 지나치게 유사한 기사 자동 삭제")

    except Exception as exc:
        print(f"[ERROR] 기사 임베딩 생성 실패 (article_id={article_id}): {exc}")
    finally:
        db.close()


# 기사 저장 전 임베딩 생성 + 유사한 기사 필터링한 뒤 한번에 저장
async def create_article_embeddings(results: list[dict]):
    db = SessionLocal()
    THRESHOLD = 0.25

    to_create = []  # 필터링된 기사를 저장할 배열

    try:
        for result in results:
            # 각 기사에 대해 임베딩 생성 요청
            embedding, _ = await generate_article_embedding(result)

            # DB 내에 유사한 기사 존재하면 저장 안 하고 넘어감
            if embedding is not None and article_crud.exists_similar_article(
                db,
                datetime.now() - timedelta(hours=24),
                0,
                embedding,
                THRESHOLD,
            ):
                print(f"[DELETE] DB 내 지나치게 유사한 기사 존재: {result["title"]}")
                continue

            # 같은 배치 내에 유사한 기사가 존재하면 저장 안 하고 넘어감
            exists_similar_in_batch = False
            for tc in to_create:
                cd = cosine_distances(
                    np.array(embedding).reshape(1, -1),
                    np.array(tc["embedding"]).reshape(1, -1),
                )
                print(cd)  # test
                if cd <= THRESHOLD:
                    exists_similar_in_batch = True
                    print(
                        f"[DELETE] 배치 내 지나치게 유사한 기사 존재: {result["title"]}, 유사도 {cd}"
                    )
                    break

            if exists_similar_in_batch:
                continue

            result["embedding"] = embedding
            to_create.append(result)

        # 유사도 필터링에 통과한 기사들만 DB에 저장
        article_crud.create_articles(db, to_create)

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

        _, behavior_embedding = await get_or_create_user_embedding(db, user)

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
