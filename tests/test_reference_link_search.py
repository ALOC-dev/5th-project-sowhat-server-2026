# ── 참고 링크 매핑 + 웹 검색 테스트 ───────────────────────────

from unittest.mock import AsyncMock, patch

import pytest

import app.services.llm.tavily_client as tavily_client
from app.services.llm.reference_links import resolve_reference_links
from app.services.llm.trusted_domains import TRUSTED_DOMAINS, is_trusted_url
from app.services.llm.tavily_client import (
    search_link_name,
    search_link_names,
)

# ── 목록 매핑 ────────────────────────────────────────────────


def test_목록에_있는_이름은_주소로_바뀐다():
    links, unmatched = resolve_reference_links(["국세청 홈택스"])

    assert links == [{"title": "국세청 홈택스", "url": "https://hometax.go.kr"}]
    assert unmatched == []


# 예전 구현은 목록에 없는 이름을 그냥 버려서 검색에 넘길 값이 없었다
def test_목록에_없는_이름은_검색용으로_반환된다():
    links, unmatched = resolve_reference_links(["창원시 공식 누리집"])

    assert links == []
    assert unmatched == ["창원시 공식 누리집"]


def test_매칭과_미매칭이_섞여도_나뉜다():
    links, unmatched = resolve_reference_links(["정부24", "창원시 공식 누리집"])

    assert [link["title"] for link in links] == ["정부24"]
    assert unmatched == ["창원시 공식 누리집"]


def test_빈_입력은_빈_결과를_반환한다():
    assert resolve_reference_links([]) == ([], [])
    assert resolve_reference_links(None) == ([], [])


def test_공백_이름은_무시된다():
    links, unmatched = resolve_reference_links(["  ", "정부24"])

    assert [link["title"] for link in links] == ["정부24"]
    assert unmatched == []


# ── 도메인 화이트리스트 ──────────────────────────────────────


@pytest.mark.parametrize(
    "url",
    [
        "https://www.mois.go.kr",
        "https://www.lh.or.kr/main",
        "https://www.kist.re.kr",
        "https://www.snu.ac.kr",
        "https://www.sec.gov/edgar",
        "https://dart.fss.or.kr",
        "https://www.krx.co.kr",
    ],
)
def test_신뢰_도메인은_통과한다(url):
    assert is_trusted_url(url) is True


@pytest.mark.parametrize(
    "url",
    [
        "https://blog.naver.com/fake-gov",
        "https://www.evil.com/go.kr",  # 경로에만 go.kr이 있는 위장 주소
        "https://go.kr.evil.com",  # 호스트 앞부분만 흉내낸 주소
        "javascript:alert(1)",
        "",
        None,
    ],
)
def test_신뢰할_수_없는_주소는_차단된다(url):
    assert is_trusted_url(url) is False


# ── 웹 검색 ──────────────────────────────────────────────────


@pytest.fixture
def fake_client():
    with patch.object(tavily_client, "get_client") as get_client:
        client = AsyncMock()
        get_client.return_value = client
        yield client


# 예전에는 검색 결과를 파이썬이 직접 골랐다(가장 얕은 링크 우선).
# 지금은 신뢰 도메인으로 검색 범위를 좁힌 뒤 결과에 번호를 붙여 LLM이 고르게 한다.


# LLM이 주소를 지어내지 못하도록 후보에 번호를 붙여 넘긴다
async def test_검색_결과에_0부터_번호가_붙는다(fake_client):
    fake_client.search.return_value = {
        "results": [
            {"url": "https://www.changwon.go.kr", "title": "창원시"},
            {"url": "https://www.changwon.go.kr/depart", "title": "창원시 부서"},
        ]
    }

    response = await search_link_name("창원시")

    assert response["query"] == "창원시"
    assert [result["index"] for result in response["results"]] == [0, 1]
    # 원래 필드는 그대로 남는다
    assert response["results"][0]["url"] == "https://www.changwon.go.kr"


async def test_검색_결과가_없으면_빈_dict를_반환한다(fake_client):
    fake_client.search.return_value = {"results": []}

    assert await search_link_name("없는기관") == {}


# 검색 결과를 그대로 쓰면 LLM이 주소를 지어내는 것과 위험이 비슷해진다
async def test_신뢰_도메인으로_검색_범위를_제한한다(fake_client):
    fake_client.search.return_value = {"results": [{"url": "https://www.mois.go.kr"}]}

    await search_link_name("행정안전부")

    _, kwargs = fake_client.search.call_args
    assert kwargs["include_domains"] == TRUSTED_DOMAINS


async def test_이름마다_한_번씩_검색해_모아준다(fake_client):
    async def fake_search(query, **kwargs):
        return {"results": [{"url": f"https://www.{query}.go.kr"}]}

    fake_client.search.side_effect = fake_search

    responses = await search_link_names(["창원시", "수원시"])

    assert [response["query"] for response in responses] == ["창원시", "수원시"]
    assert fake_client.search.await_count == 2


# API 키가 없는 환경에서도 서버가 죽지 않아야 한다
async def test_API_키가_없으면_검색을_건너뛴다():
    with patch.object(tavily_client, "get_client", return_value=None):
        assert await search_link_names(["창원시"]) == []


async def test_검색할_이름이_없으면_검색하지_않는다(fake_client):
    assert await search_link_names([]) == []
    assert fake_client.search.await_count == 0
