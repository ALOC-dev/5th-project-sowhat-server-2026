# ── 참고 링크 매핑 + 웹 검색 테스트 ───────────────────────────

from unittest.mock import AsyncMock, patch

import pytest

import app.services.llm.tavily_client as tavily_client
from app.services.llm.reference_links import resolve_reference_links
from app.services.llm.trusted_domains import is_trusted_url
from app.services.llm.tavily_client import (
    search_official_url,
    search_reference_links,
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


async def test_검색_결과_중_신뢰_도메인만_채택한다(fake_client):
    fake_client.search.return_value = {
        "results": [
            {"url": "https://blog.naver.com/aaa"},
            {"url": "https://www.changwon.go.kr"},
        ]
    }

    assert await search_official_url("창원시") == "https://www.changwon.go.kr"


# 검색은 기관의 게시판 페이지를 먼저 물어오는 경우가 많아 메인을 우선한다
async def test_신뢰_도메인_중_가장_얕은_링크를_고른다(fake_client):
    fake_client.search.return_value = {
        "results": [
            {"url": "https://www.mois.go.kr/frt/bbs/type010/list.do?bbsId=BBS001"},
            {"url": "https://www.mois.go.kr/frt/a01/intro.do"},
            {"url": "https://www.mois.go.kr"},
        ]
    }

    assert await search_official_url("행정안전부") == "https://www.mois.go.kr"


# 깊이만 보고 고르면 '창원시' 검색에 더 얕은 '수원시' 메인이 잡혀 기관이 뒤바뀐다
async def test_다른_기관의_더_얕은_링크에_속지_않는다(fake_client):
    fake_client.search.return_value = {
        "results": [
            {"url": "https://www.changwon.go.kr/depart/main.do"},
            {"url": "https://www.suwon.go.kr"},
        ]
    }

    assert await search_official_url("창원시") == "https://www.changwon.go.kr/depart/main.do"


async def test_같은_깊이면_쿼리스트링_없는_쪽을_고른다(fake_client):
    fake_client.search.return_value = {
        "results": [
            {"url": "https://www.kdca.go.kr/board?menuId=10"},
            {"url": "https://www.kdca.go.kr/board"},
        ]
    }

    assert await search_official_url("질병관리청") == "https://www.kdca.go.kr/board"


async def test_신뢰_도메인이_없으면_None(fake_client):
    fake_client.search.return_value = {
        "results": [{"url": "https://blog.naver.com/aaa"}]
    }

    assert await search_official_url("창원시") is None


# 링크는 해설의 부가 정보라 검색이 실패해도 해설 자체는 나가야 한다
async def test_검색이_실패해도_예외를_던지지_않는다(fake_client):
    fake_client.search.side_effect = RuntimeError("타임아웃")

    assert await search_official_url("창원시") is None


async def test_찾은_이름만_링크로_묶인다(fake_client):
    async def fake_search(query, max_results):
        if "창원시" in query:
            return {"results": [{"url": "https://www.changwon.go.kr"}]}
        return {"results": [{"url": "https://blog.naver.com/aaa"}]}

    fake_client.search.side_effect = fake_search

    links = await search_reference_links(["창원시", "없는기관"])

    assert links == [{"title": "창원시", "url": "https://www.changwon.go.kr"}]


# API 키가 없는 환경에서도 서버가 죽지 않아야 한다
async def test_API_키가_없으면_검색을_건너뛴다():
    with patch.object(tavily_client, "get_client", return_value=None):
        assert await search_reference_links(["창원시"]) == []
        assert await search_official_url("창원시") is None
