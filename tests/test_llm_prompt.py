from datetime import datetime
from types import SimpleNamespace

import pytest

import app.services.llm_service as llm_service
from app.schemas.common_analysis import CommonAnalysis, KeywordItem
from app.schemas.personal_analysis import (
    LinkSearchTarget,
    PersonalAnalysisBeforeSearch,
)
from app.services.llm.prompts import (
    COMMON_ANALYSIS_PROMPT,
    PERSONAL_ANALYSIS_PROMPT,
)
from app.services.search.reference_links import REFERENCE_LINK_NAMES
from app.services.llm_service import (
    generate_common_analysis,
    generate_personal_analysis,
)


# enum 값이 한국어로 바뀌어 .value가 그대로 프롬프트에 들어간다
def fake_article_namespace():
    return SimpleNamespace(
        title="경제뉴스",
        category=SimpleNamespace(value="경제"),
        content="국내 증시 변동성이 커지고 있다.",
        summary="국내 증시 변동성이 커지고 있습니다.",
    )


def fake_user_namespace():
    return SimpleNamespace(
        age=20,
        gender=SimpleNamespace(value="남"),
        region=SimpleNamespace(value="서울"),
        job=SimpleNamespace(value="학생"),
        interest=SimpleNamespace(value="경제"),
        purpose=SimpleNamespace(value="공부"),
        filtered_extra_information="주식 투자를 처음 시작한 대학생이다.",
    )


# 공통 해설 프롬프트에 기사 정보와 출력 키가 잘 들어가는지 확인
def test_common_analysis_prompt_contains_article_info():
    prompt = COMMON_ANALYSIS_PROMPT.format(
        title="경제뉴스",
        category="경제",
        content="국내 증시 변동성이 커지고 있다.",
    )

    assert "뉴스 해설가" in prompt
    assert "제목: 경제뉴스" in prompt
    assert "카테고리: 경제" in prompt
    assert "본문: 국내 증시 변동성이 커지고 있다." in prompt
    assert "요약문 작성 규칙" in prompt
    assert "키워드 작성 규칙" in prompt


# 개인 맞춤 해설 프롬프트에 기사 정보 + 사용자 정보 + 참고 자료가 잘 들어가는지 확인
def test_personal_analysis_prompt_contains_user_profile():
    prompt = PERSONAL_ANALYSIS_PROMPT.format(
        title="경제뉴스",
        category="경제",
        summary="국내 증시 변동성이 커지고 있습니다.",
        related_articles="없음",
        reference_links=REFERENCE_LINK_NAMES,
        age=20,
        gender="남",
        region="서울",
        job="학생",
        interest="경제",
        purpose="공부",
        extra_information="주식 투자를 처음 시작한 대학생이다.",
    )

    assert "개인 맞춤형 뉴스 해설가" in prompt
    assert "제목: 경제뉴스" in prompt
    assert "카테고리: 경제" in prompt
    assert "요약문: 국내 증시 변동성이 커지고 있습니다." in prompt
    # 저작권 문제로 본문은 저장하지 않으므로 개인해설 입력에 본문이 없어야 한다
    assert "본문:" not in prompt
    assert "나이: 20" in prompt
    assert "성별: 남" in prompt
    assert "지역: 서울" in prompt
    assert "직업: 학생" in prompt
    assert "관심사: 경제" in prompt
    assert "뉴스 소비 목적: 공부" in prompt
    assert "추가 정보: 주식 투자를 처음 시작한 대학생이다." in prompt
    assert "effect 작성 규칙" in prompt
    assert "solution 작성 규칙" in prompt
    assert "link_targets 작성 규칙" in prompt
    assert "source_name" in prompt
    assert "search_purpose" in prompt
    # 링크 허용 목록이 프롬프트에 포함되어야 LLM이 목록 밖 이름을 만들지 않는다
    assert "금융감독원 전자공시시스템" in prompt


# 과거 유사 기사가 프롬프트의 <참고 자료>에 들어가는지 확인
def test_format_related_articles():
    assert llm_service.format_related_articles([]) == "없음"
    assert llm_service.format_related_articles(None) == "없음"

    related = SimpleNamespace(
        published_at=datetime(2026, 5, 1),
        title="증시 변동성 확대",
        summary="지난해에도 증시 변동성이 커졌습니다.",
    )
    formatted = llm_service.format_related_articles([related])

    assert "2026년 05월 01일" in formatted
    assert "증시 변동성 확대" in formatted
    assert "지난해에도 증시 변동성이 커졌습니다." in formatted


# 공통 해설 LLM 함수 테스트
# 실제 OpenAI 호출 없이 monkeypatch로 가짜 응답을 넣고
# keyword가 [{"word": ..., "description": ...}] 리스트로 반환되는지 확인
@pytest.mark.asyncio
async def test_generate_common_analysis_returns_keyword_list(monkeypatch):
    fake_parsed = CommonAnalysis(
        summary="국내 증시 변동성이 커지면서 개인 투자자들의 관심이 높아지고 있다.",
        keyword=[
            KeywordItem(word="증시", description="주식을 사고파는 시장을 말한다."),
            KeywordItem(word="변동성", description="가격이 오르내리는 정도를 말한다."),
        ],
    )

    fake_response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(parsed=fake_parsed))]
    )

    async def fake_create_json_completion(messages, response_format):
        assert response_format is CommonAnalysis
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

        user_prompt = messages[1]["content"]
        assert "제목: 경제뉴스" in user_prompt
        assert "카테고리: ECONOMY" in user_prompt
        assert "국내 증시 변동성이 커지고 있다." in user_prompt

        return fake_response

    monkeypatch.setattr(
        llm_service, "create_json_completion", fake_create_json_completion
    )

    result = await generate_common_analysis(
        {
            "title": "경제뉴스",
            "content": "국내 증시 변동성이 커지고 있다.",
            "category": "ECONOMY",
        }
    )

    assert result["summary"] == fake_parsed.summary
    assert result["keyword"] == [
        {"word": "증시", "description": "주식을 사고파는 시장을 말한다."},
        {"word": "변동성", "description": "가격이 오르내리는 정도를 말한다."},
    ]


# 개인 맞춤 해설 LLM 함수 테스트
# 실제 OpenAI 호출 없이 monkeypatch로 가짜 응답을 넣고
# 사용자 정보가 프롬프트에 반영되고 결과가 정상 반환되는지 확인
@pytest.mark.asyncio
async def test_generate_personal_analysis_returns_result(monkeypatch):
    fake_parsed = PersonalAnalysisBeforeSearch(
        effect="이 뉴스는 경제에 관심 있는 학생에게 투자 시장의 변동성을 이해하는 데 도움이 될 수 있다.",
        solution="관련 기업의 공시를 금융감독원 전자공시시스템에서 확인해 보세요.",
        link_targets=[
            LinkSearchTarget(
                source_name="금융감독원 전자공시시스템",
                search_purpose="기업 공시",
            ),
            LinkSearchTarget(
                source_name="국가통계포털",
                search_purpose="경제 지표",
            ),
        ],
    )

    fake_response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(parsed=fake_parsed))]
    )

    async def fake_create_json_completion(messages, response_format):
        assert response_format is PersonalAnalysisBeforeSearch
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

        user_prompt = messages[1]["content"]
        assert "제목: 경제뉴스" in user_prompt
        assert "카테고리: 경제" in user_prompt
        assert "나이: 20" in user_prompt
        assert "성별: 남" in user_prompt
        assert "지역: 서울" in user_prompt
        assert "직업: 학생" in user_prompt
        assert "관심사: 경제" in user_prompt
        # 과거 유사 기사가 <참고 자료>로 전달되어야 한다
        assert "증시 변동성 확대" in user_prompt

        return fake_response

    monkeypatch.setattr(
        llm_service, "create_json_completion", fake_create_json_completion
    )

    fake_article = fake_article_namespace()
    fake_user = fake_user_namespace()
    fake_related = [
        SimpleNamespace(
            published_at=datetime(2026, 5, 1),
            title="증시 변동성 확대",
            summary="지난해에도 증시 변동성이 커졌습니다.",
        )
    ]

    result = await generate_personal_analysis(fake_article, fake_user, fake_related)

    assert result["effect"] == fake_parsed.effect
    assert result["solution"] == fake_parsed.solution
    # 1차 해설은 창구 '이름'까지만 만든다. 주소는 검색·선택 단계에서 붙는다
    assert result["link_names"] == ["금융감독원 전자공시시스템", "국가통계포털"]
    assert "links" not in result


# 이 단계는 이름을 그대로 넘길 뿐이라 목록에 있는 이름인지 따지지 않는다.
# 주소를 찾는 일은 select_search_result가 맡는다.
@pytest.mark.asyncio
async def test_generate_personal_analysis_passes_unknown_link_name_through(monkeypatch):
    fake_parsed = PersonalAnalysisBeforeSearch(
        effect="효과",
        solution="해결책",
        link_targets=[
            LinkSearchTarget(
                source_name="존재하지 않는 기관",
                search_purpose="공식 누리집",
            )
        ],
    )

    fake_response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(parsed=fake_parsed))]
    )

    async def fake_create_json_completion(messages, response_format):
        return fake_response

    monkeypatch.setattr(
        llm_service, "create_json_completion", fake_create_json_completion
    )

    result = await generate_personal_analysis(
        fake_article_namespace(), fake_user_namespace()
    )

    assert result["link_names"] == ["존재하지 않는 기관 누리집"]
    assert result["effect"] == "효과"
    assert result["solution"] == "해결책"
