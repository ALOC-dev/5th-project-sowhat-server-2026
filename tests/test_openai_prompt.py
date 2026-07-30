"""
실제 OpenAI 호출로 해설 프롬프트의 출력 품질을 눈으로 확인하는 테스트.

프롬프트 문자열은 app/services/llm/prompts.py 하나만 사용한다.
(이전에는 이 파일에 프롬프트 사본을 두고 수정해 운영 프롬프트와 내용이 갈렸다.)
"""

import pytest

from app.services.llm.openai_client import create_json_completion
from app.crud.article import find_related_past_articles, get_article_by_id
from app.crud.user import get_user_by_id
from app.db.database import SessionLocal

from app.schemas.common_analysis import CommonAnalysis
from app.schemas.personal_analysis import PersonalAnalysisBeforeSearch, SelectedIndex
from app.schemas.filtered_extra_information import FilteredExtraInformation
from app.services.llm.prompts import (
    COMMON_ANALYSIS_PROMPT,
    PERSONAL_ANALYSIS_PROMPT,
    SYSTEM_JSON_PROMPT,
    FILTER_EXTRA_INFORMATION_PROMPT,
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
            links, unmatched = resolve_reference_links(parsed["link_names"])

            print(f"\n[개인맞춤해설: 사용자 {id}]")
            print("effect:", parsed["effect"])
            print("solution:", parsed["solution"])
            print("link_names:", parsed["link_names"] or "없음")
            for link in links:
                print(f"  - {link['title']} {link['url']}")
            if unmatched:
                print("  (목록에 없어 검색으로 넘어갈 이름):", unmatched)

            # 등록된 창구 이름만 링크로 변환되고, 나머지는 검색 대상으로 남는다
            assert len(links) + len(unmatched) == len(parsed["link_names"])
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

LINK_SEARCH_PROMPT = """
너는 뉴스 해설에서 제안된 사용자 행동(솔루션)에 대해, 실제로 클릭해서 이동할 수 있는 가장 적합한 참고 링크 하나를 <검색 결과 목록> 중에서 선택해야 한다.
사용자는 이 링크를 눌러 <솔루션>에서 제안한 행동(조회, 신청, 확인 등)을 실제로 수행하려 한다.
잘못되거나 관련 없는 링크를 제공하면 사용자가 혼란을 겪거나 잘못된 정보로 행동할 수 있으므로, 관련성이 확실하지 않으면 링크를 반환하지 않는 것이 링크를 잘못 반환하는 것보다 낫다.

<검색 결과 목록>에는 번호(index)가 매겨져 있다.
가장 적합한 항목의 번호와 관련도 점수를 다음 형식으로 반환하라. 
{{'index': 선택한 항목의 번호 (없으면 -1), 'score': 관련도 점수}}
<선택 규칙>을 반드시 지켜라.

<선택 규칙>
- <검색 결과 목록>의 각 항목 중 <검색어> 및 <솔루션>의 의도와 가장 관련 있는 것 하나를 선택하라.
- <검색 결과 목록>에 실제로 존재하는 index만 선택하라. 목록에 없는 index를 만들어내지 마라.
- 선택한 검색 결과가 <솔루션>과 얼마나 관련있고 적합한지를 1~3점으로 평가하라.
  - 3점: 사용자가 <솔루션>에서 제안한 행동(조회/신청/확인)을 실제로 수행할 수 있는 해당 기관/기업의 구체적인 페이지
  - 2점: 관련 기관 또는 기업의 페이지이지만 구체적인 행동 페이지인지는 불확실 (예: 홈페이지 메인)
  - 1점: 단순 뉴스 보도, 블로그, 언론사의 재인용 기사 등 사용자가 직접 행동할 수 없는 페이지
- 관련도 점수가 1점이면 'index'로 -1을 반환한다.
- 동일 점수의 후보가 여럿이면 아래 우선순위에 따라 선택한다:
  1. .go.kr, .or.kr 등 공식 기관/공공 도메인
  2. 해당 기업·기관의 자체 도메인 (제3자 재게시 페이지보다 우선)
  3. 정보가 더 최신인 페이지
- 기사나 홍보성 콘텐츠보다 사용자가 실제로 입력/조회/신청 등을 할 수 있는 서비스형 페이지를 우선하라.
</선택 규칙>

<솔루션>
{solution}
</솔루션>

<검색어>
{search_query}
</검색어>

<검색 결과 목록>
{search_results}
</검색 결과 목록>
""".strip()


async def test_select_search_result():

    solution = ""
    search_query = ""
    search_results = []

    prompt = LINK_SEARCH_PROMPT.format(
        solution=solution,
        search_query=search_query,
        search_results=search_results,
    )

    response = await create_json_completion(
        messages=[
            {"role": "system", "content": SYSTEM_JSON_PROMPT},
            {"role": "user", "content": prompt},
        ],
        response_format=SelectedIndex,
    )

    parsed = response.choices[0].message.parsed.model_dump()
    print(**parsed)
