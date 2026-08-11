from datetime import datetime
import numpy as np

from app.models.article import Article
from app.models.user import User
from app.schemas.common_analysis import CommonAnalysis
from app.schemas.filtered_extra_information import FilteredExtraInformation
from app.schemas.personal_analysis import (
    LinkSelectionResult,
    PersonalAnalysisBeforeSearch,
)
from app.services.llm.openai_client import create_json_completion, get_embedding
from app.services.llm.prompts import (
    COMMON_ANALYSIS_PROMPT,
    PERSONAL_ANALYSIS_PROMPT,
    SYSTEM_JSON_PROMPT,
    FILTER_EXTRA_INFORMATION_PROMPT,
    LINK_SEARCH_PROMPT,
)
from app.services.search.trusted_links import TRUSTED_LINK_NAMES
from app.services.search.tavily_client import (
    search_link_targets,
)

from app.schemas.common_analysis import CommonAnalysis
from app.schemas.personal_analysis import PersonalAnalysisBeforeSearch


# 카테고리는 nullable이므로 값이 없을 수 있다.
# 프롬프트가 빈 값을 받으면 기사 내용에 맞는 카테고리를 직접 채우도록 되어 있다.
def category_value(category) -> str:
    return category.value if category is not None else ""


async def generate_common_analysis(article: Article | dict) -> dict:
    # SQLAlchemy 모델에는 model_dump()가 없으므로 필요한 필드만 꺼내 dict로 변환
    if type(article) is Article:
        article = {
            "title": article.title,
            "category": category_value(article.category),
            "content": article.content,
        }

    prompt = COMMON_ANALYSIS_PROMPT.format(
        title=article["title"],
        category=article["category"],
        content=article["content"],
    )

    ### OpenAI
    response = await create_json_completion(
        messages=[
            {"role": "system", "content": SYSTEM_JSON_PROMPT},
            {"role": "user", "content": prompt},
        ],
        response_format=CommonAnalysis,
    )

    parsed = response.choices[0].message.parsed.model_dump()

    return parsed


# 과거 유사 기사를 프롬프트에 넣을 문자열로 변환
def format_related_articles(related_articles: list[Article] | None) -> str:
    if not related_articles:
        return "없음"

    return "\n".join(
        f"- ({article.published_at:%Y년 %m월 %d일}) {article.title}\n  {article.summary}"
        for article in related_articles
    )


async def generate_personal_analysis(
    article: Article,
    user: User,
    related_articles: list[Article] | None = None,
) -> dict:
    # 개인해설은 요약문을 기사 골자로 삼으므로 요약이 없으면 먼저 생성한다
    summary = article.summary
    if summary is None:
        common_analysis = await generate_common_analysis(article)
        summary = common_analysis["summary"]

    prompt = PERSONAL_ANALYSIS_PROMPT.format(
        title=article.title,
        category=category_value(article.category),
        summary=summary,
        related_articles=format_related_articles(related_articles),
        reference_links=TRUSTED_LINK_NAMES,
        username=user.username,
        age=user.age,
        gender=user.gender.value,
        region=user.region.value,
        job=user.job.value,
        interest=user.interest.value,
        purpose=user.purpose.value,
        extra_information=user.filtered_extra_information,
    )

    response = await create_json_completion(
        messages=[
            {"role": "system", "content": SYSTEM_JSON_PROMPT},
            {"role": "user", "content": prompt},
        ],
        response_format=PersonalAnalysisBeforeSearch,
    )

    parsed = response.choices[0].message.parsed.model_dump()

    """
    returns: dict
        {
            "effect": str,
            "solution": str,
            "links": [{"title": str, "url": str}],
            "link_targets": [
                {"source_name": str, "search_purpose": str},
            ],
        }
    """
    return parsed


async def select_search_result(
    solution: str,
    link_targets: list[dict],
) -> list[dict]:

    if link_targets == []:
        return []

    time_start = datetime.now()
    all_search_responses = await search_link_targets(link_targets)
    time_elapsed = datetime.now() - time_start
    print("[Tavily 검색]", time_elapsed)

    if not all_search_responses:
        print("[ERROR] 검색 결과를 찾을 수 없음")
        return []

    selected_results = []

    time_start = datetime.now()
    for sr in all_search_responses:
        # 검색 결과 중 하나라도 예외가 발생하거나 일정 형식으로 나오지 않으면 스킵 처리
        if not isinstance(sr, dict):
            continue

        search_query = sr.get("query", None)
        search_results = sr.get("results", None)

        if not search_query or not search_results or len(search_results) == 0:
            continue

        prompt = LINK_SEARCH_PROMPT.format(
            solution=solution,
            search_query=search_query,
            search_results=search_results,
        )

        try:
            response = await create_json_completion(
                messages=[
                    {"role": "system", "content": SYSTEM_JSON_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                response_format=LinkSelectionResult,
            )
        except Exception as exc:
            print(
                "[ERROR] 검색 결과 선택 LLM 호출 실패: search_query=%s, error=%s"
                % (search_query, exc)
            )
            continue

        parsed = response.choices[0].message.parsed

        if not parsed.success or parsed.index is None:
            continue

        if not 0 <= parsed.index < len(search_results):
            print(
                "[ERROR] 검색 결과 선택 index 범위 오류: search_query=%s, index=%s, count=%s"
                % (search_query, parsed.index, len(search_results))
            )
            continue

        selection = search_results[parsed.index]

        # 검색 결과의 제목에서 필요없는 문자를 없앤다.
        selection["title"] = (
            selection["title"].replace("\n", "").replace("\r", "").replace("\t", "")
        )

        print(
            "[INFO] 검색 결과 선택 완료: search_query=%s, index=%s, score=%s, title=%s, url=%s"
            % (
                search_query,
                parsed.index,
                parsed.score,
                selection["title"],
                selection["url"],
            )
        )

        # 이미 있는 링크와 같으면 버린다.
        selected_urls = [sr["url"][: sr["url"].index("?")] for sr in selected_results]

        if selection["url"] in selected_urls:
            print("[SKIP] 중복 링크")
            continue

        selected_results.append(
            {
                "title": selection["title"],
                "url": selection["url"],
            }
        )
    time_elapsed = datetime.now() - time_start
    print("[검색 결과 선정]", time_elapsed)

    return selected_results


# 채팅으로 사용자 추가정보 필터링을 요청하는 함수
async def filter_user_extra_information(
    extra_information: str,
) -> FilteredExtraInformation:
    normalized_information = extra_information.strip()

    if not normalized_information:
        return FilteredExtraInformation(
            success=True,
            summary="",
        )

    response = await create_json_completion(
        messages=[
            {
                "role": "developer",
                "content": FILTER_EXTRA_INFORMATION_PROMPT,
            },
            {
                "role": "user",
                "content": normalized_information,
            },
        ],
        response_format=FilteredExtraInformation,
    )

    return response.choices[0].message.parsed


# 기사 임베딩 생성 함수
# LLM으로 생성된 기사 요약본을 통해 임베딩 생성 (+필요시 해설 생성)
async def generate_article_embedding(article: Article | dict):
    # SQLAlchemy 모델에는 model_dump()가 없으므로 필요한 필드만 꺼내 dict로 변환
    if type(article) is Article:
        article = {
            "title": article.title,
            "category": category_value(article.category),
            "content": article.content,
            "summary": article.summary,
        }

    # 기사 요약 불러오기, 없을 시 생성해서 함께 반환
    if article["summary"] is None:
        common_analysis = await generate_common_analysis(article)
        summary = common_analysis["summary"]
        is_analysis_created = True
    else:
        summary = article["summary"]
        is_analysis_created = False

    embeddings = await get_embedding(summary)
    article_embedding = embeddings[0]
    article_embedding /= np.linalg.norm(article_embedding)  # 벡터 정규화

    return article_embedding, (common_analysis if is_analysis_created else {})


# 사용자 프로필 정보 임베딩 생성 함수
# 처음 회원가입할 때 및 기사 추천시 사용자 임베딩이 없을 때 호출
async def generate_user_profile_embedding(user: User) -> list[float]:
    # 사용자 프로필 정보를 자연스러운 구어체 문장형으로 묘사하여 초기 프로필 임베딩 생성
    profile_text = [
        f"이 사용자는 {user.age}세이며, 성별은 {user.gender.value}자입니다.",
        f"현재 직업은 {user.job.value}이며, 주로 {user.region.value} 지역의 소식에 관심이 있습니다.",
        f"평소에 {user.interest.value} 분야의 뉴스를 즐겨 읽습니다.",
        f"뉴스를 읽는 주된 목적은 {user.purpose.value}입니다.",
        f"추가적인 사용자 성향 정보는 다음과 같습니다: {user.extra_information}",
    ]
    embeddings = await get_embedding(
        profile_text
    )  # 각 프로필 항목에 대한 임베딩을 리스트로 반환

    """
    각 임베딩을 다음 비율로 가중합하고 정규화해 사용자 프로필 임베딩을 구한다.
    (0) 나이/성별 0.1
    (1) 직업/지역 0.2
    (2) 관심사 0.3
    (3) 목적 0.2
    (4) 추가 정보 0.2
    """
    profile_embedding = (
        embeddings[0] * 0.1
        + embeddings[1] * 0.2
        + embeddings[2] * 0.3
        + embeddings[3] * 0.2
        + embeddings[4] * 0.2
    )
    profile_embedding /= np.linalg.norm(profile_embedding)  # 정규화

    return profile_embedding
