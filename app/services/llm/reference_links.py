"""
개인해설의 조회/신청 링크로 사용할 공식 창구 목록.

LLM이 주소를 직접 생성하면 존재하지 않는 링크를 만들 위험이 있으므로,
LLM에는 창구 이름만 고르게 하고 실제 주소는 서버에서 매핑한다.
새 창구를 추가할 때는 반드시 실제 주소를 확인한 뒤 등록한다.

목록에 없는 창구 이름은 여기서 링크로 바뀌지 않는다.
그 이름들은 웹 검색(Tavily) 단계에서 실제 링크를 찾는 검색어로 사용한다.
"""

REFERENCE_LINKS: dict[str, str] = {
    "금융감독원 전자공시시스템": "https://dart.fss.or.kr",
    "한국거래소": "https://www.krx.co.kr",
    "미국 증권거래위원회 전자공시시스템": "https://www.sec.gov/edgar",
    "한국석유공사 오피넷": "https://www.opinet.co.kr",
    "한국은행 경제통계시스템": "https://ecos.bok.or.kr",
    "국가통계포털": "https://kosis.kr",
    "고용노동부 워크넷": "https://www.work24.go.kr",
    "정부24": "https://www.gov.kr",
    "국세청 홈택스": "https://hometax.go.kr",
    "국민건강보험공단": "https://www.nhis.or.kr",
    "국민연금공단": "https://www.nps.or.kr",
    "법제처 국가법령정보센터": "https://www.law.go.kr",
}

# 프롬프트에 넣을 허용 목록 문자열
REFERENCE_LINK_NAMES = "\n".join(f"- {name}" for name in REFERENCE_LINKS)


# LLM이 고른 이름을 실제 주소로 변환한다. 목록에 없으면 빈 문자열을 반환한다.
def resolve_reference_link(link_name: str | None) -> str:
    if not link_name:
        return ""

    return REFERENCE_LINKS.get(link_name.strip(), "")


# 창구 이름 목록을 {title, url} 목록으로 변환한다.
# 목록에 없는 이름은 링크를 만들 수 없으므로 제외한다.
def resolve_reference_links(link_names: list[str] | None) -> list[dict]:
    if not link_names:
        return []

    links = []

    for name in link_names:
        url = resolve_reference_link(name)

        if url:
            links.append({"title": name.strip(), "url": url})

    return links
