"""
실제 OpenAI 호출로 해설 프롬프트의 출력 품질을 눈으로 확인하는 테스트.

프롬프트 문자열은 app/services/llm/prompts.py 하나만 사용한다.
(이전에는 이 파일에 프롬프트 사본을 두고 수정해 운영 프롬프트와 내용이 갈렸다.)
"""

import json

import pytest

from app.services.llm.openai_client import create_json_completion
from app.crud.article import find_related_past_articles, get_article_by_id
from app.crud.user import get_user_by_id
from app.db.database import SessionLocal

from app.schemas.common_analysis import CommonAnalysis
from app.schemas.personal_analysis import (
    LinkSelectionResult,
    PersonalAnalysisBeforeSearch,
)
from app.schemas.filtered_extra_information import FilteredExtraInformation
from app.services.llm.prompts import (
    COMMON_ANALYSIS_PROMPT,
    PERSONAL_ANALYSIS_PROMPT,
    SYSTEM_JSON_PROMPT,
    FILTER_EXTRA_INFORMATION_PROMPT,
    LINK_SEARCH_PROMPT,
)
from app.services.llm.reference_links import (
    REFERENCE_LINK_NAMES,
    resolve_reference_links,
)
from app.services.llm_service import category_value, format_related_articles

# 테스트 기사 5, 6, 18, 209, 347, 359, 371, 391, 509, 587, 742, 1026, 1045, 1110
# 5(경제, ▲ 열거 항목), 509(정치, 지엽적 소재로 개인화되던 사례)는 피드백에서 지적된 기사
# 1026은 과거 유사 기사가 있어 참고 자료 인용을 확인할 수 있는 기사
TEST_ARTICLE_IDS = [5, 509, 1026]
TEST_USER_IDS = [1, 2, 4]


# 공통해설 생성 (개인해설 테스트에서 요약문 입력으로도 사용)
async def generate_summary(article) -> dict:
    prompt = COMMON_ANALYSIS_PROMPT.format(
        title=article.title,
        category=category_value(article.category),
        content=article.content,
    ).strip()

    response = await create_json_completion(
        messages=[
            {"role": "system", "content": SYSTEM_JSON_PROMPT},
            {"role": "user", "content": prompt},
        ],
        response_format=CommonAnalysis,
    )

    return response.choices[0].message.parsed.model_dump()


# 기사 원문을 보고서에 붙일 수 있는 형태로 출력
def print_article(article) -> None:
    print(f"\n{'=' * 70}")
    print(f"기사 {article.id}")
    print(f"{'=' * 70}")
    print("\n[기사 원문]")
    print(article.title)
    print()
    print(article.content)


@pytest.mark.live
async def test_common_analysis_prompt():
    db = SessionLocal()

    for article_id in TEST_ARTICLE_IDS:
        test_article = get_article_by_id(db, article_id)
        parsed = await generate_summary(test_article)

        print_article(test_article)
        print("\n[공통해설]")
        print("'summary':", repr(parsed["summary"]))
        print("'keyword':", parsed["keyword"])
        print("\n[이전 버전 요약]")
        print(test_article.summary)

        assert parsed["success"]


@pytest.mark.live
async def test_personal_analysis_prompt():
    db = SessionLocal()

    for article_id in TEST_ARTICLE_IDS:
        test_article = get_article_by_id(db, article_id)

        # DB에 저장된 요약문은 이전 버전 프롬프트로 생성된 것이므로 새로 생성해 사용
        summary = (await generate_summary(test_article))["summary"]

        # 과거 유사 기사 검색 (임베딩이 없는 기사는 빈 목록이 된다)
        related_articles = find_related_past_articles(db, test_article)

        print_article(test_article)
        print("\n[개인해설 입력 요약문]")
        print(summary)
        print("\n[참고 자료(과거 유사 기사)]")
        for related in related_articles:
            print(f"- ({related.published_at:%Y-%m-%d}) {related.id} {related.title}")
        if not related_articles:
            print("없음")

        for id in TEST_USER_IDS:
            test_user = get_user_by_id(db, id)

            prompt = PERSONAL_ANALYSIS_PROMPT.format(
                title=test_article.title,
                category=category_value(test_article.category),
                summary=summary,
                related_articles=format_related_articles(related_articles),
                reference_links=REFERENCE_LINK_NAMES,
                age=test_user.age,
                gender=test_user.gender.value,
                region=test_user.region.value,
                job=test_user.job.value,
                interest=test_user.interest.value,
                purpose=test_user.purpose.value,
                extra_information=test_user.filtered_extra_information,
            ).strip()

            response = await create_json_completion(
                messages=[
                    {"role": "system", "content": SYSTEM_JSON_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                response_format=PersonalAnalysisBeforeSearch,
            )
            parsed = response.choices[0].message.parsed.model_dump()
            links = resolve_reference_links(parsed["link_names"])

            print(f"\n[개인맞춤해설: 사용자 {id}]")
            print("effect:", parsed["effect"])
            print("solution:", parsed["solution"])
            print("link_names:", parsed["link_names"] or "없음")
            for link in links:
                print(f"  - {link['title']} {link['url']}")

            # 등록된 창구 이름만 링크로 변환된다
            assert len(links) <= len(parsed["link_names"])
        print()


# FILTER_EXTRA_INFORMATION_PROMPT 검증용 (필요할 때만 실행)
# async def test_filtering_prompt():
#     test_extra_information_list = [
#         "취업 준비 중이라 IT 산업 뉴스에 관심이 많습니다. 아 근데, 내일 밥 뭐 먹지. 집 주소는 서울시 동대문구 어디어디구요. 채용 정보에 대한 뉴스를 많이 보고 싶습니다.",
#         "컴퓨터공학을 공부하고 있으며, 월월월 그르릉 안녕하세요 개 입니다, 경제 뉴스에 대한 이해가 부족한 편입니다.",
#         "투자에 관심이 있어 관련 뉴스와 분석을 보고 싶습니다. 제 계좌번호는 123-456-7890입니다.",
#     ]

#     for test_extra_information in test_extra_information_list:
#         response = await create_json_completion(
#             messages=[
#                 {
#                     "role": "developer",
#                     "content": FILTER_EXTRA_INFORMATION_PROMPT,
#                 },
#                 {
#                     "role": "user",
#                     "content": test_extra_information.strip(),
#                 },
#             ],
#             response_format=FilteredExtraInformation,
#         )

#         result = response.choices[0].message.parsed

#         print("\n[사용자 입력]")
#         print(test_extra_information)
#         print("[필터링 결과]")
#         print(result.model_dump())


@pytest.mark.live
async def test_link_search_prompt():
    test_cases = [
        {
            "name": "공식 기관 페이지 선택",
            "solution": (
                "청년 지원 정책의 신청 조건과 접수 일정을 "
                "고용노동부 공식 누리집에서 확인해 보세요."
            ),
            "search_query": "고용노동부 청년 지원 정책",
            "category": "사회",
            "search_results": [
                {
                    "index": 0,
                    "title": "청년 지원 정책 후기와 신청 팁",
                    "url": "https://example-blog.com/youth-policy",
                    "category": "사회",
                },
                {
                    "index": 1,
                    "title": "고용노동부 청년정책 안내",
                    "url": "https://www.moel.go.kr/youth-policy",
                    "category": "사회",
                },
                {
                    "index": 2,
                    "title": "청년 고용 관련 뉴스",
                    "url": "https://example-news.com/youth-employment",
                    "category": "사회",
                },
            ],
            "expected_index": 1,
        },
        {
            "name": "관련 결과 없음",
            "solution": (
                "국민연금공단 공식 누리집에서 "
                "예상 연금액과 가입 내역을 확인해 보세요."
            ),
            "search_query": "국민연금공단 예상 연금액",
            "category": "경제",
            "search_results": [
                {
                    "index": 0,
                    "title": "국내 주식시장 전망",
                    "url": "https://example.com/stock",
                    "category": "경제",
                },
                {
                    "index": 1,
                    "title": "퇴직연금 상품 비교",
                    "url": "https://example.com/retirement",
                    "category": "경제",
                },
            ],
            "expected_index": None,
        },
    ]

    for test_case in test_cases:
        prompt = LINK_SEARCH_PROMPT.format(
            solution=test_case["solution"],
            search_query=test_case["search_query"],
            category=test_case["category"],
            search_results=json.dumps(
                test_case["search_results"],
                ensure_ascii=False,
                indent=2,
            ),
        )

        response = await create_json_completion(
            messages=[
                {"role": "system", "content": SYSTEM_JSON_PROMPT},
                {"role": "user", "content": prompt},
            ],
            response_format=LinkSelectionResult,
        )

        parsed = response.choices[0].message.parsed

        print(f"\n[{test_case['name']}]")
        print("solution:", test_case["solution"])
        print("search_query:", test_case["search_query"])
        print("search_results:", test_case["search_results"])
        print("selection:", parsed.model_dump())

        if test_case["expected_index"] is None:
            assert parsed.success is False
            assert parsed.index is None
            assert parsed.score is None
        else:
            assert parsed.success is True
            assert parsed.index == test_case["expected_index"]
            assert parsed.score is not None
            assert parsed.score >= 3
