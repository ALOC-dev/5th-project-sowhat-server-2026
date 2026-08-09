from types import SimpleNamespace
from unittest.mock import AsyncMock
from urllib.parse import urlparse

import pytest

import app.services.article as article_service
import app.services.search.tavily_client as tavily_client
from app.schemas.personal_analysis import LinkSearchTarget
from app.services.search.trusted_links import TRUSTED_DOMAINS


def target(source_name: str, search_purpose: str) -> dict:
    return {
        "source_name": source_name,
        "search_purpose": search_purpose,
    }


def test_link_search_target_parses_source_and_purpose():
    parsed = LinkSearchTarget(
        source_name="Financial Supervisory Service",
        search_purpose="company disclosure",
    )

    assert parsed.source_name == "Financial Supervisory Service"
    assert parsed.search_purpose == "company disclosure"


@pytest.mark.asyncio
async def test_search_target_combines_fields_for_tavily(monkeypatch):
    client = AsyncMock()
    client.search.return_value = {"results": []}
    monkeypatch.setattr(tavily_client, "get_client", lambda: client)

    await tavily_client.search_link_target(
        target("Financial Supervisory Service", "company disclosure")
    )

    client.search.assert_awaited_once_with(
        "Financial Supervisory Service company disclosure",
        include_domains=TRUSTED_DOMAINS,
        max_results=tavily_client.MAX_SEARCH_RESULTS,
    )


@pytest.mark.asyncio
async def test_registered_source_searches_purpose_in_its_domain(monkeypatch):
    client = AsyncMock()
    client.search.return_value = {
        "results": [
            {
                "title": "external result",
                "url": "https://example.com/economic-indicator",
            }
        ]
    }
    monkeypatch.setattr(tavily_client, "get_client", lambda: client)

    result = await tavily_client.search_link_target(
        target("한국은행 경제통계시스템", "경제지표")
    )

    assert result == {}
    client.search.assert_awaited_once_with(
        "경제지표",
        include_domains=["ecos.bok.or.kr"],
        max_results=tavily_client.MAX_SEARCH_RESULTS,
    )


@pytest.mark.asyncio
async def test_searches_each_link_target(monkeypatch):
    client = AsyncMock()
    client.search.side_effect = [
        {"results": []},
        {"results": []},
    ]
    monkeypatch.setattr(tavily_client, "get_client", lambda: client)

    await tavily_client.search_link_targets(
        [
            target("Service A", "purpose A"),
            target("Service B", "purpose B"),
        ]
    )

    assert [call.args[0] for call in client.search.await_args_list] == [
        "Service A purpose A",
        "Service B purpose B",
    ]


@pytest.mark.asyncio
async def test_empty_link_targets_skip_search(monkeypatch):
    def fail_get_client():
        raise AssertionError("client lookup must be skipped")

    monkeypatch.setattr(tavily_client, "get_client", fail_get_client)

    assert await tavily_client.search_link_targets([]) == []


@pytest.mark.asyncio
async def test_article_removes_link_targets_from_final_response(monkeypatch):
    article = SimpleNamespace(
        title="title",
        category=SimpleNamespace(value="economy"),
    )
    user = SimpleNamespace()
    link_targets = [target("Service A", "purpose A")]
    created = {}

    monkeypatch.setattr(
        article_service.article_crud,
        "get_article_by_id",
        lambda db, article_id: article,
    )
    monkeypatch.setattr(
        article_service.user_crud,
        "get_user_by_id",
        lambda db, user_id: user,
    )
    monkeypatch.setattr(
        article_service.personal_crud,
        "get_analysis_by_article_and_user",
        lambda db, article_id, user_id: None,
    )
    monkeypatch.setattr(
        article_service.article_crud,
        "find_related_past_articles",
        lambda db, current_article: [],
    )

    async def fake_generate(current_article, current_user, related_articles):
        return {
            "effect": "effect",
            "solution": "solution",
            "link_targets": link_targets,
        }

    async def fake_select(solution, received_targets):
        assert solution == "solution"
        assert received_targets == link_targets
        return [{"title": "result", "url": "https://example.go.kr"}]

    def fake_create(db, payload):
        created.update(payload)

    monkeypatch.setattr(article_service, "generate_personal_analysis", fake_generate)
    monkeypatch.setattr(article_service, "select_search_result", fake_select)
    monkeypatch.setattr(article_service.personal_crud, "create_analysis", fake_create)

    background_tasks = SimpleNamespace(add_task=lambda *args: None)
    result = await article_service.get_personal_analysis(
        object(), 1, 2, background_tasks
    )

    assert "link_targets" not in result
    assert "link_targets" not in created
    assert result["links"] == [{"title": "result", "url": "https://example.go.kr"}]


@pytest.mark.asyncio
async def test_select_search_result_passes_link_targets_to_tavily(monkeypatch):
    import app.services.llm_service as llm_service

    link_targets = [
        target("Service A", "purpose A"),
        target("Service B", "purpose B"),
    ]
    received = {}

    async def fake_search(received_targets):
        received["targets"] = received_targets
        return []

    monkeypatch.setattr(llm_service, "search_link_targets", fake_search)

    assert await llm_service.select_search_result("solution", link_targets) == []
    assert received["targets"] == link_targets


@pytest.mark.live
@pytest.mark.parametrize(
    ("source_name", "search_purpose"),
    [
        ("한국은행 경제통계시스템", "경제지표"),
        ("금융감독원 전자공시시스템", "삼성전자 공시"),
        ("K-Sight 무역보험 빅데이터 플랫폼", "국외기업 공시자료"),
        ("고용24", "채용정보"),
        ("산업통상자원부", "산업 정책"),
    ],
)
@pytest.mark.asyncio
async def test_live_registered_targets_search_only_the_purpose(
    source_name, search_purpose, monkeypatch
):
    if not tavily_client.settings.TAVILY_API_KEY:
        pytest.skip("TAVILY_API_KEY is not configured")

    client = tavily_client.AsyncTavilyClient(
        api_key=tavily_client.settings.TAVILY_API_KEY
    )
    monkeypatch.setattr(tavily_client, "get_client", lambda: client)

    response = await tavily_client.search_link_target(
        target(source_name, search_purpose)
    )

    expected_domain = tavily_client.TRUSTED_HOSTS[source_name]
    print("\n" + "=" * 80)
    print("[SOURCE]", source_name)
    print("[SEARCH PURPOSE]", search_purpose)
    print("[TAVILY QUERY]", response.get("query"))
    print("[INCLUDE DOMAIN]", expected_domain)
    for result in response.get("results", []):
        print(
            f"[{result['index'] + 1}]",
            f"score={result.get('score')}",
            result.get("title"),
        )
        print("   ", result.get("url"))

    assert response, "No Tavily response was returned from the official domain."
    assert response.get("query") == search_purpose
    assert response.get("results"), "No search results were returned for inspection."

    normalized_expected = expected_domain.removeprefix("www.")
    result_hosts = [
        (urlparse(result["url"]).hostname or "").removeprefix("www.")
        for result in response["results"]
    ]
    assert all(
        host == normalized_expected or host.endswith(f".{normalized_expected}")
        for host in result_hosts
    )
