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
from app.schemas.personal_analysis import (
    PersonalAnalysisBeforeSearch,
    LinkSelectionResult,
)
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


# # 공통해설 생성 (개인해설 테스트에서 요약문 입력으로도 사용)
# async def generate_summary(article) -> dict:
#     prompt = COMMON_ANALYSIS_PROMPT.format(
#         title=article.title,
#         category=category_value(article.category),
#         content=article.content,
#     ).strip()

#     response = await create_json_completion(
#         messages=[
#             {"role": "system", "content": SYSTEM_JSON_PROMPT},
#             {"role": "user", "content": prompt},
#         ],
#         response_format=CommonAnalysis,
#     )

#     return response.choices[0].message.parsed.model_dump()


# # 기사 원문을 보고서에 붙일 수 있는 형태로 출력
# def print_article(article) -> None:
#     print(f"\n{'=' * 70}")
#     print(f"기사 {article.id}")
#     print(f"{'=' * 70}")
#     print("\n[기사 원문]")
#     print(article.title)
#     print()
#     print(article.content)


# @pytest.mark.live
# async def test_common_analysis_prompt():
#     db = SessionLocal()

#     for article_id in TEST_ARTICLE_IDS:
#         test_article = get_article_by_id(db, article_id)
#         parsed = await generate_summary(test_article)

#         print_article(test_article)
#         print("\n[공통해설]")
#         print("'summary':", repr(parsed["summary"]))
#         print("'keyword':", parsed["keyword"])
#         print("\n[이전 버전 요약]")
#         print(test_article.summary)

#         assert parsed["success"]


# @pytest.mark.live
# async def test_personal_analysis_prompt():
#     db = SessionLocal()

#     for article_id in TEST_ARTICLE_IDS:
#         test_article = get_article_by_id(db, article_id)

#         # DB에 저장된 요약문은 이전 버전 프롬프트로 생성된 것이므로 새로 생성해 사용
#         summary = (await generate_summary(test_article))["summary"]

#         # 과거 유사 기사 검색 (임베딩이 없는 기사는 빈 목록이 된다)
#         related_articles = find_related_past_articles(db, test_article)

#         print_article(test_article)
#         print("\n[개인해설 입력 요약문]")
#         print(summary)
#         print("\n[참고 자료(과거 유사 기사)]")
#         for related in related_articles:
#             print(f"- ({related.published_at:%Y-%m-%d}) {related.id} {related.title}")
#         if not related_articles:
#             print("없음")

#         for id in TEST_USER_IDS:
#             test_user = get_user_by_id(db, id)

#             prompt = PERSONAL_ANALYSIS_PROMPT.format(
#                 title=test_article.title,
#                 category=category_value(test_article.category),
#                 summary=summary,
#                 related_articles=format_related_articles(related_articles),
#                 reference_links=REFERENCE_LINK_NAMES,
#                 age=test_user.age,
#                 gender=test_user.gender.value,
#                 region=test_user.region.value,
#                 job=test_user.job.value,
#                 interest=test_user.interest.value,
#                 purpose=test_user.purpose.value,
#                 extra_information=test_user.filtered_extra_information,
#             ).strip()

#             response = await create_json_completion(
#                 messages=[
#                     {"role": "system", "content": SYSTEM_JSON_PROMPT},
#                     {"role": "user", "content": prompt},
#                 ],
#                 response_format=PersonalAnalysisBeforeSearch,
#             )
#             parsed = response.choices[0].message.parsed.model_dump()
#             links, unmatched = resolve_reference_links(parsed["link_names"])

#             print(f"\n[개인맞춤해설: 사용자 {id}]")
#             print("effect:", parsed["effect"])
#             print("solution:", parsed["solution"])
#             print("link_names:", parsed["link_names"] or "없음")
#             for link in links:
#                 print(f"  - {link['title']} {link['url']}")
#             if unmatched:
#                 print("  (목록에 없어 검색으로 넘어갈 이름):", unmatched)

#             # 등록된 창구 이름만 링크로 변환되고, 나머지는 검색 대상으로 남는다
#             assert len(links) + len(unmatched) == len(parsed["link_names"])
#         print()


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

from app.services.llm.prompts import LINK_SEARCH_PROMPT
from app.services.llm.tavily_client import get_client
from app.services.llm.trusted_domains import TRUSTED_SUFFIXES, TRUSTED_HOSTS


async def test_select_search_result():
    db = SessionLocal()

    for article_id in TEST_ARTICLE_IDS:
        for user_id in TEST_USER_IDS:
            test_article = get_article_by_id(db, article_id)
            test_user = get_user_by_id(db, user_id)

            prompt = PERSONAL_ANALYSIS_PROMPT.format(
                title=test_article.title,
                category=category_value(test_article.category),
                summary=test_article.summary,
                related_articles="없음",
                reference_links=REFERENCE_LINK_NAMES,
                age=test_user.age,
                gender=test_user.gender.value,
                region=test_user.region.value,
                job=test_user.job.value,
                interest=test_user.interest.value,
                purpose=test_user.purpose.value,
                extra_information=test_user.filtered_extra_information,
            )

            test_analysis = await create_json_completion(
                messages=[
                    {"role": "system", "content": SYSTEM_JSON_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                response_format=PersonalAnalysisBeforeSearch,
            )
            parsed = test_analysis.choices[0].message.parsed.model_dump()
            print(parsed)
            print()

            if len(parsed["link_names"]) == 0:
                print("=" * 60)
                continue

            tavily_client = get_client()

            for link_name in parsed["link_names"]:
                include_domains = [
                    *TRUSTED_HOSTS,
                    *(suffix.lstrip(".") for suffix in TRUSTED_SUFFIXES),
                ]

                search_response = await tavily_client.search(
                    link_name,
                    include_domains=include_domains,
                    max_results=5,
                )

                print(search_response.get("query"))
                search_results = [
                    {
                        "index": search_response.get("results").index(result),
                        "title": result.get("title"),
                        "url": result.get("url"),
                        "content": result.get("content"),
                    }
                    for result in search_response.get("results")
                ]
                for result in search_results:
                    print(result["index"], "/", result["title"], "/", result["url"])
                print()

                prompt = LINK_SEARCH_PROMPT.format(
                    solution=parsed["solution"],
                    search_query=search_response.get("query"),
                    search_results=search_results,
                )

                select_response = await create_json_completion(
                    messages=[
                        {"role": "system", "content": SYSTEM_JSON_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    response_format=LinkSelectionResult,
                )

                select_parsed = select_response.choices[0].message.parsed.model_dump()
                print(select_parsed)
                if select_parsed["success"]:
                    print(search_results[select_parsed["index"]])

                print("=" * 60)


# async def test_search_user_action():
#     from app.services.llm.reference_links import REFERENCE_LINK_NAMES

#     test_solutions = [
#         "서울에 사는 20대 청년이라면 본인이 청년 월세 지원을 받을 수 있는 대상인지 확인해 보세요.",
#         "미국 증권거래위원회 전자공시시스템에서 엔비디아의 공시를 확인해 보세요.",
#         "국내 시장 반응도 함께 보려면 한국거래소에서 반도체 관련 종목과 기술주 흐름을 비교해 보세요.",
#         "국내 유가 흐름은 한국석유공사 오피넷에서 확인하고, 보유 중인 미국 반도체 관련 기업의 공시에서 에너지 비용, 공급망, 지정학적 위험 언급이 있는지 미국 증권거래위원회 전자공시시스템에서 점검해 보세요.",
#         "물가 부담이 커지는지 보려면 한국은행 경제통계시스템에서 소비자물가 관련 지표를 함께 점검해 보세요.",
#         "주식 공부를 할 때는 이번 기사처럼 에너지 공급 위험이 커졌다는 뉴스와 실제 유가, 물가 지표가 같은 방향으로 움직이는지 기록해 보세요.",
#         "이 기사는 투자 결정보다 공부용으로, 공항 운영 중단과 석유 시설 피해가 실제로 후속 보도에서 어떻게 확인되는지 비교해 보세요.",
#     ]

#     for solution in test_solutions:
#         prompt = f"""
#         <effect>
#         빈칸으로 남겨 둔다.
#         </effect>

#         <solution>
#         {solution}
#         </solution>

#         <link_names 작성 규칙>
#         - link_names는 solution에서 사용자가 할 수 있는 행동의 수에 따라 최대 2개까지 작성한다. 항목이 2개일 때는 사용자가 먼저 실행해야 할 행동을 앞에 둔다.
#         - link_names의 항목 하나는 사용자가 검색창에 그대로 입력할 검색어 하나다.
#         - 각 검색어는 [창구] + [대상] + [찾을 정보] 순서로 붙인다. 창구가 없으면 [대상] + [찾을 정보]만 쓴다.
#         - 대상이 특정 기업, 제도, 지표 등이 아닌 불확실한 것을 가리킨다면 [대상] 부분을 생략한다.
#         - [찾을 정보]에는 동사가 아니라 명사를 쓴다. 대상, 요건, 조건, 방법, 공시, 시세, 가격, 일정, 현황 등
#         - 검색어는 반드시 명사로 끝낸다. 다음 단어는 검색어에 쓰지 않는다: 확인, 점검, 비교, 파악, 검토, 분석, 살펴보기, 알아보기, 흐름
#         solution에 이 단어들이 있어도 검색어에는 옮기지 않는다.
#         - 예외적으로 solution이 사용자의 적극적 참여를 요구할 때만 그 동작을 명사형으로 넣는다.
#         허용 단어: 신청, 접수, 가입, 신고, 등록, 예약, 발급, 모집
#         이 목록에 없는 동작은 넣지 않는다.
#         - 한 행동 안에 등장하는 기관명과 대상(기업, 제도, 지표 등)을 별개 항목으로 쪼개지 않는다.
#         - 조사와 서술어는 빼고 명사 위주로 6어절 이내로 쓴다.
#         - 아래 목록에 있는 창구를 안내했다면 목록에 적힌 이름을 그대로 포함한다.
#         - 목록에 없는 창구를 안내했다면 solution에 쓴 공식 명칭을 그대로 포함한다. 명칭을 새로 지어내지 않는다.
#         - 안내한 창구가 없거나 확인 대상이 후속 보도뿐이면 link_names를 빈 목록으로 둔다.
#         - 주소(URL)는 절대 작성하지 않는다.
#         [목록]
#         {REFERENCE_LINK_NAMES}
#         </link_names 작성 규칙>
#         """

#         link_names = await create_json_completion(
#             messages=[
#                 {"role": "system", "content": SYSTEM_JSON_PROMPT},
#                 {"role": "user", "content": prompt},
#             ],
#             response_format=PersonalAnalysisBeforeSearch,
#         )

#         parsed = link_names.choices[0].message.parsed.model_dump()
#         print("solution:", parsed["solution"])
#         print("link_names:", parsed["link_names"])
#         print()

#         tavily_client = get_client()

#         for link_name in parsed["link_names"]:
#             search_response = await tavily_client.search(link_name, max_results=5)

#             search_results = [
#                 {
#                     "index": search_response.get("results").index(result),
#                     "title": result.get("title"),
#                     "url": result.get("url"),
#                     "content": result.get("content"),
#                 }
#                 for result in search_response.get("results")
#             ]
#             for result in search_results:
#                 print(result["index"], "/", result["title"], "/", result["url"])
#             print()

#             prompt = LINK_SEARCH_PROMPT.format(
#                 solution=solution,
#                 search_query=search_response.get("query"),
#                 search_results=search_results,
#             )

#             select_response = await create_json_completion(
#                 messages=[
#                     {"role": "system", "content": SYSTEM_JSON_PROMPT},
#                     {"role": "user", "content": prompt},
#                 ],
#                 response_format=LinkSelectionResult,
#             )

#             parsed = select_response.choices[0].message.parsed.model_dump()
#             print(parsed)
#             if parsed["success"]:
#                 print(search_results[parsed["index"]])
#             print()

#         print("=" * 60)
