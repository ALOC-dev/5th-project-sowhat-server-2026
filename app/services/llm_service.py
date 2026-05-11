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
- summary는 기사 핵심 내용을 2~3문장으로 요약한다.
- 어려운 표현은 쉬운 표현으로 바꾼다.
- 원문에 없는 사실을 추가하지 않는다.
- 추측성 표현은 최소화한다.
- keyword는 기사 이해에 가장 중요한 용어 1개만 작성한다.
- keyword는 설명 없이 용어만 작성한다.
- keyword는 너무 일반적인 단어가 아니라 기사 핵심과 직접 연결되는 용어여야 한다.
- 불필요한 설명, 서론, 부가 문장은 쓰지 않는다.
- 반드시 JSON 형식으로만 출력한다.
- JSON 외의 다른 문장은 절대 출력하지 않는다.

[출력 형식]
{
  "summary": "string",
  "keyword": "string"
}

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
- effect는 "이 뉴스가 왜 이 사용자와 관련이 있는지"가 드러나야 한다.
- 사용자 정보와 무관한 일반론만 작성하지 않는다.
- 사용자의 지역, 나이, 성별, 직업, 관심사를 가능한 범위에서 반영한다.
- 기사와 사용자 정보의 관련성이 약하면 억지로 연결하지 말고, 과장하지 않는다.
- solution은 사용자가 실제로 할 수 있는 확인, 준비, 대응 행동 중심으로 작성한다.
- 과장되거나 불확실한 조언은 하지 않는다.
- 기사 원문에 없는 사실을 만들어내지 않는다.
- 투자, 법률, 의료처럼 고위험 판단을 단정적으로 제시하지 않는다.
- 가능하면 공식 확인이 필요하다는 방향으로 작성한다.
- effect와 solution은 각각 2~3문장으로 작성한다.
- 불필요한 설명, 서론, 부가 문장은 쓰지 않는다.
- 반드시 JSON 형식으로만 출력한다.
- JSON 외의 다른 문장은 절대 출력하지 않는다.

[출력 형식]
{
  "effect": "string",
  "solution": "string"
}

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

async def generate_common_analysis_with_groq(
    title: str,
    content: str,
    category: str | None = None,
):
    prompt = COMMON_ANALYSIS_PROMPT.format(
        title=title,
        category=category or "미분류",
        content=content,
    )

    response = await client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {"role": "system", "content": "너는 JSON만 출력하는 뉴스 해설 도우미다."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )

    raw_text = response.choices[0].message.content.strip()
    return json.loads(raw_text)


async def generate_personal_analysis_with_groq(
    title: str,
    content: str,
    user_profile: dict,
    category: str | None = None,
):
    prompt = PERSONAL_ANALYSIS_PROMPT.format(
        title=title,
        category=category or "미분류",
        content=content,
        age=user_profile["age"],
        gender=user_profile["gender"],
        region=user_profile["region"],
        job=user_profile["job"],
        interest=user_profile["interest"],
    )

    response = await client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {"role": "system", "content": "너는 JSON만 출력하는 뉴스 해설 도우미다."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )

    raw_text = response.choices[0].message.content.strip()
    return json.loads(raw_text)