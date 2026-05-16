import json
from groq import AsyncGroq
from app.core.config import settings

client = AsyncGroq(api_key=settings.GROQ_API_KEY)

COMMON_ANALYSIS_PROMPT = """
너는 뉴스 해설 서비스의 공통 해설 생성기다.

입력된 뉴스 기사 정보를 바탕으로, 모든 사용자가 공통적으로 이해할 수 있는 해설을 생성해야 한다.

반드시 아래 규칙을 지켜라.

[목표]
1. 기사 내용을 쉬운 말로 요약한다.
2. 기사 이해에 가장 중요한 핵심 용어 1개를 선택한다.

[작성 규칙]
- summary는 기사 핵심 내용을 최대 3문장 또는 200자 이내로 요약한다.
- 기사 본문에 없는 내용, 추론, 확대 해석은 추가하지 않는다.
- 원문을 단순 복붙하지 말고 자연스럽게 정리한다.
- 같은 의미를 반복하지 않는다.
- 어려운 표현은 쉬운 표현으로 바꾼다.
- keyword는 기사 핵심과 직접 관련된 용어 1개만 작성한다.
- keyword에는 설명을 포함하지 않는다.
- 문자열 내부에 큰따옴표(") 사용이 필요하면 작은따옴표(')로 대체한다.
- 반드시 아래 JSON 형식만 출력한다.

[출력 형식]
{{
  "summary": "string",
  "keyword": "string"
}}

[기사 정보]
제목: {title}
카테고리: {category}
본문: {content}
""".strip()

PERSONAL_ANALYSIS_PROMPT = """
너는 뉴스 해설 서비스의 개인 맞춤 해설 생성기다.

입력된 뉴스 기사 정보와 사용자 정보를 바탕으로, 해당 사용자에게 맞는 영향 분석과 대응 방안을 생성해야 한다.

반드시 아래 규칙을 지켜라.

[목표]
1. 뉴스가 이 사용자에게 어떤 영향을 주는지 설명한다.
2. 사용자가 확인하거나 준비할 수 있는 대응 방안을 제시한다.

[작성 규칙]
- effect는 기사 내용과 사용자 정보를 연결해서 작성한다.
- 사용자와 관련성이 약하면 과장해서 연결하지 않는다.
- solution은 실제로 할 수 있는 행동 중심으로 작성한다.
- 기사 원문에 없는 사실을 만들지 않는다.
- 투자, 법률, 의료 관련 판단을 단정적으로 제시하지 않는다.
- effect와 solution은 각각 2~3문장으로 작성한다.
- 문자열 내부에 큰따옴표(") 사용이 필요하면 작은따옴표(')로 대체한다.
- 반드시 아래 JSON 형식만 출력한다.

[출력 형식]
{{
  "effect": "string",
  "solution": "string"
}}

[기사 정보]
제목: {title}
카테고리: {category}
본문: {content}

[사용자 정보]
나이: {age}
성별: {gender}
지역: {region}
직업: {job}
관심사: {interest}
""".strip()

SYSTEM_JSON_PROMPT = (
    "모든 응답은 json.loads()로 바로 파싱 가능한 JSON 형식이어야 한다. "
    "JSON 외의 설명문, 코드블럭, 마크다운, 주석은 출력하지 마라."
)


async def generate_common_analysis_with_groq(article_data: dict):
    prompt = COMMON_ANALYSIS_PROMPT.format(
        title=article_data["title"],
        category=article_data["category"],
        content=article_data["content"],
    )

    response = await client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_JSON_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )

    raw_text = response.choices[0].message.content.strip()

    raw_text = raw_text.replace("```json", "").replace("```", "").strip()

    print(raw_text)  # LLM 답변 원문 확인용

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as exc:
        print(f"[JSON ERROR] {exc}")
        print(raw_text)

        return {"summary": "해설 생성 실패", "keyword": "오류"}


async def generate_personal_analysis_with_groq(article_data: dict, user_profile: dict):
    prompt = PERSONAL_ANALYSIS_PROMPT.format(
        title=article_data["title"],
        category=article_data["category"],
        content=article_data["content"],
        age=user_profile["age"],
        gender=user_profile["gender"],
        region=user_profile["region"],
        job=user_profile["job"],
        interest=user_profile["interest"],
    )

    response = await client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_JSON_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )

    raw_text = response.choices[0].message.content.strip()

    raw_text = raw_text.replace("```json", "").replace("```", "").strip()

    print(raw_text)  # LLM 답변 원문 확인용

    try:
        return json.loads(raw_text)

    except json.JSONDecodeError as exc:
        print(f"[JSON ERROR] {exc}")
        print(raw_text)

        return {"effect": "해설 생성 실패", "solution": "잠시 후 다시 시도해주세요."}
