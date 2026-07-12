from types import SimpleNamespace

import pytest

import app.services.llm_service as llm_service
from app.schemas.common_analysis import CommonAnalysis, KeywordItem
from app.schemas.personal_analysis import PersonalAnalysis
from app.services.llm.prompts import (
    COMMON_ANALYSIS_PROMPT,
    PERSONAL_ANALYSIS_PROMPT,
)
from app.services.llm_service import (
    generate_common_analysis,
    generate_personal_analysis,
)


# 공통 해설 프롬프트에 기사 정보와 출력 키가 잘 들어가는지 확인
def test_common_analysis_prompt_contains_article_info():
    prompt = COMMON_ANALYSIS_PROMPT.format(
        title="경제뉴스",
        category="ECONOMY",
        content="국내 증시 변동성이 커지고 있다.",
    )

    assert "너는 뉴스 해설 서비스의 공통 해설 생성기다." in prompt
    assert "제목: 경제뉴스" in prompt
    assert "카테고리: ECONOMY" in prompt
    assert "본문: 국내 증시 변동성이 커지고 있다." in prompt
    assert "summary" in prompt
    assert "keyword" in prompt


# 개인 맞춤 해설 프롬프트에 기사 정보 + 사용자 정보 + 출력 키가 잘 들어가는지 확인
def test_personal_analysis_prompt_contains_user_profile():
    prompt = PERSONAL_ANALYSIS_PROMPT.format(
        title="경제뉴스",
        category="ECONOMY",
        content="국내 증시 변동성이 커지고 있다.",
        age=20,
        gender="MALE",
        region="SEOUL",
        job="STUDENT",
        interest="ECONOMY",
        purpose="HABIT",
        extra_information="주식 투자를 처음 시작한 대학생이다.",
    )

    assert "너는 뉴스 해설 서비스의 개인 맞춤 해설 생성기다." in prompt
    assert "제목: 경제뉴스" in prompt
    assert "카테고리: ECONOMY" in prompt
    assert "본문: 국내 증시 변동성이 커지고 있다." in prompt
    assert "나이: 20" in prompt
    assert "성별: MALE" in prompt
    assert "지역: SEOUL" in prompt
    assert "직업: STUDENT" in prompt
    assert "관심사: ECONOMY" in prompt
    assert "뉴스 소비 목적: HABIT" in prompt
    assert "추가 정보: 주식 투자를 처음 시작한 대학생이다." in prompt
    assert '"effect"' in prompt
    assert '"solution"' in prompt


# 공통 해설 LLM 함수 테스트
# 실제 OpenAI 호출 없이 monkeypatch로 가짜 응답을 넣고
# keyword가 {"단어": "뜻 설명"} dict로 변환되는지 확인
@pytest.mark.asyncio
async def test_generate_common_analysis_returns_keyword_dict(monkeypatch):
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
    assert result["keyword"] == {
        "증시": "주식을 사고파는 시장을 말한다.",
        "변동성": "가격이 오르내리는 정도를 말한다.",
    }


# 개인 맞춤 해설 LLM 함수 테스트
# 실제 OpenAI 호출 없이 monkeypatch로 가짜 응답을 넣고
# 사용자 정보가 프롬프트에 반영되고 결과가 정상 반환되는지 확인
@pytest.mark.asyncio
async def test_generate_personal_analysis_returns_result(monkeypatch):
    fake_parsed = PersonalAnalysis(
        effect="이 뉴스는 경제에 관심 있는 학생에게 투자 시장의 변동성을 이해하는 데 도움이 될 수 있다.",
        solution="관련 내용을 공식 금융 정보나 신뢰할 수 있는 경제 뉴스에서 추가로 확인하는 것이 좋다.",
    )

    fake_response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(parsed=fake_parsed))]
    )

    async def fake_create_json_completion(messages, response_format):
        assert response_format is PersonalAnalysis
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

        user_prompt = messages[1]["content"]
        assert "제목: 경제뉴스" in user_prompt
        assert "카테고리: ECONOMY" in user_prompt
        assert "나이: 20" in user_prompt
        assert "성별: MALE" in user_prompt
        assert "지역: SEOUL" in user_prompt
        assert "직업: STUDENT" in user_prompt
        assert "관심사: ECONOMY" in user_prompt

        return fake_response

    monkeypatch.setattr(
        llm_service, "create_json_completion", fake_create_json_completion
    )

    fake_article = SimpleNamespace(
        title="경제뉴스",
        category="ECONOMY",
        content="국내 증시 변동성이 커지고 있다.",
    )
    fake_user = SimpleNamespace(
        age=20,
        gender="MALE",
        region="SEOUL",
        job="STUDENT",
        interest="ECONOMY",
        purpose="HABIT",
        filtered_extra_information="주식 투자를 처음 시작한 대학생이다.",
    )

    result = await generate_personal_analysis(fake_article, fake_user)

    assert result["effect"] == fake_parsed.effect
    assert result["solution"] == fake_parsed.solution
