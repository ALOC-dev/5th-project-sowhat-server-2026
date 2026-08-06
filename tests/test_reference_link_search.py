# ── 참고 링크 매핑 + 웹 검색 테스트 ───────────────────────────

from unittest.mock import AsyncMock, patch

import pytest

import app.services.llm.tavily_client as tavily_client
from app.services.llm.reference_links import resolve_reference_links
from app.services.llm.trusted_domains import is_trusted_url
from app.services.llm.tavily_client import search_link_targets

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




async def test_여러_검색_대상을_각각_검색한다(fake_client):
    async def fake_search(query, include_domains, max_results):
        return {"results": [{"url": f"https://example.go.kr/{query}"}]}

    fake_client.search.side_effect = fake_search

    results = await search_link_targets(
        [
            {"source_name": "창원시", "search_purpose": "공식 누리집"},
            {"source_name": "없는기관", "search_purpose": "공식 누리집"},
        ]
    )

    assert [result["query"] for result in results] == [
        "창원시 공식 누리집",
        "없는기관 공식 누리집",
    ]

# API 키가 없는 환경에서도 서버가 죽지 않아야 한다
async def test_API_키가_없으면_검색을_건너뛴다():
    with patch.object(tavily_client, "get_client", return_value=None):
        assert await search_link_targets(
            [{"source_name": "창원시", "search_purpose": "공식 누리집"}]
        ) == []
