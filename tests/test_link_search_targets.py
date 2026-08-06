from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

import app.services.article as article_service
import app.services.llm.tavily_client as tavily_client
from app.schemas.personal_analysis import LinkSearchTarget
from app.services.llm.trusted_domains import TRUSTED_DOMAINS


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
    assert result["links"] == [
        {"title": "result", "url": "https://example.go.kr"}
    ]


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
