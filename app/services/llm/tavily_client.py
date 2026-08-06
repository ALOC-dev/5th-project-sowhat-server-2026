"""
REFERENCE_LINKS 목록에 없는 창구 이름을 웹 검색해 실제 주소를 찾는다.

LLM이 주소를 지어내지 않도록 이름만 고르게 한 뒤, 그 이름을 검색어로 쓴다.
검색 결과 중 신뢰 도메인(trusted_domains)에 해당하는 첫 링크만 채택한다.
링크는 해설의 부가 정보이므로 검색이 실패하거나 느리면 링크 없이 넘어간다.
"""

import asyncio
from urllib.parse import urlparse

from tavily import AsyncTavilyClient

from app.core.config import settings
from app.services.llm.trusted_domains import TRUSTED_DOMAINS, is_trusted_url

# 검색 1건당 대기 한도(초). 개인해설 응답 지연을 막기 위해 짧게 잡는다.
SEARCH_TIMEOUT = 5.0

# 최대 검색 건수
MAX_SEARCH_RESULTS = 5

_client: AsyncTavilyClient | None = None


def get_client() -> AsyncTavilyClient | None:
    global _client

    if not settings.TAVILY_API_KEY:
        return None

    if _client is None:
        _client = AsyncTavilyClient(api_key=settings.TAVILY_API_KEY)

    return _client


# 링크가 얼마나 깊은 페이지인지 재는 값. 작을수록 메인에 가깝다.
# 경로 깊이를 먼저 보고, 같으면 쿼리스트링 있는 쪽을 뒤로 민다.
# def url_depth(url: str) -> tuple[int, int, int]:
#     parsed = urlparse(url)
#     segments = [s for s in parsed.path.split("/") if s]

#     return len(segments), 1 if parsed.query else 0, len(url)


# 창구 이름 하나를 검색해 신뢰 도메인의 공식 주소를 찾는다. 없으면 None.
# async def search_official_url(link_name: str) -> str | None:
#     client = get_client()

#     if client is None:
#         return None

#     try:
#         async with asyncio.timeout(SEARCH_TIMEOUT):
#             response = await client.search(
#                 query=f"{link_name} 공식 홈페이지",
#                 max_results=5,
#             )
#     except Exception as exc:
#         print(f"[WARN] 링크 검색 실패({link_name}): {exc}")
#         return None

#     trusted = [
#         result["url"]
#         for result in response.get("results", [])
#         if is_trusted_url(result.get("url"))
#     ]

#     if not trusted:
#         return None

#     # 검색 순위 1위 신뢰 결과의 기관을 정답으로 본다.
#     # 깊이만 보고 고르면 '창원시'에 더 얕은 '수원시' 메인이 잡히는 식으로 기관이 뒤바뀐다.
#     host = urlparse(trusted[0]).hostname

#     # 정한 기관 안에서는 메인에 가까운 링크를 쓴다.
#     # 검색은 기관의 특정 게시판 페이지를 먼저 물어오는 경우가 많기 때문이다.
#     same_host = [url for url in trusted if urlparse(url).hostname == host]

#     return min(same_host, key=url_depth)


async def search_link_target(link_target: dict) -> dict:
    client = get_client()

    query = f"{link_target['source_name']} {link_target['search_purpose']}".strip()
    response = await client.search(
        query,
        include_domains=TRUSTED_DOMAINS,
        max_results=MAX_SEARCH_RESULTS,
    )

    results = response.get("results", [])

    if len(results) == 0:
        return {}

    # 검색 결과에 0-based index를 추가한다.
    indexed_results = [
        {"index": index, **result} for index, result in enumerate(results)
    ]

    return {"query": query, "results": indexed_results}


# 여러 창구 이름을 동시에 검색해 {query, results} 목록으로 돌려준다.
# 찾지 못한 이름은 결과에서 빠진다.
async def search_link_targets(link_targets: list[dict]) -> list[dict]:

    ## LLM이 고른 창구 이름을 등록된 주소로 바꾸고,목록에 없는 이름은 웹 검색으로 공식 주소를 찾는다.
    ## 링크는 해설의 부가 정보이므로 검색이 실패해도 매칭된 링크만 담아 응답한다.
    # links, unmatched = resolve_reference_links(link_names)

    if not link_targets or get_client() is None:
        return []

    results = await asyncio.gather(
        *(search_link_target(target) for target in link_targets),
        return_exceptions=True,
    )

    return results
