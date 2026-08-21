"""
### 참고: 이 파일의 변수 및 함수는 테스트용으로만 사용되며, 실제 검색 용도로 사용되지 않음 ###

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
    "K-Sight 무역보험 빅데이터 플랫폼": "https://ksight.ksure.or.kr",
    "한국석유공사 페트로넷": "https://www.petronet.co.kr",
    "한국석유공사 오피넷": "https://www.opinet.co.kr",
    "한국은행 경제통계시스템": "https://ecos.bok.or.kr",
    "국가통계포털": "https://kosis.kr",
    "국가데이터처": "https://mods.go.kr",
    "고용24": "https://www.work24.go.kr",
    "정부24": "https://www.gov.kr",
    "국세청 홈택스": "https://hometax.go.kr",
    "국민건강보험공단": "https://www.nhis.or.kr",
    "국민연금공단": "https://www.nps.or.kr",
    "법제처 국가법령정보센터": "https://www.law.go.kr",
    "행정안전부": "https://www.mois.go.kr",
    "기획재정부": "https://www.moef.go.kr",
    "고용노동부": "https://www.moel.go.kr",
    "보건복지부": "https://www.mohw.go.kr",
    "교육부": "https://www.moe.go.kr",
    "국토교통부": "https://www.molit.go.kr",
    "산업통상자원부": "https://www.motie.go.kr",
    "과학기술정보통신부": "https://www.msit.go.kr",
    "환경부": "https://www.me.go.kr",
    "중소벤처기업부": "https://www.mss.go.kr",
    "금융위원회": "https://www.fsc.go.kr",
    "공정거래위원회": "https://www.ftc.go.kr",
    "질병관리청": "https://www.kdca.go.kr",
    "기상청": "https://www.weather.go.kr",
    "한국소비자원": "https://www.kca.go.kr",
    "근로복지공단": "https://www.comwel.or.kr",
    "한국주택금융공사": "https://www.hf.go.kr",
    "한국토지주택공사": "https://www.lh.or.kr",
    "대한법률구조공단": "https://www.klac.or.kr",
    "국민권익위원회": "https://www.acrc.go.kr",
}

# 프롬프트에 넣을 허용 목록 문자열
REFERENCE_LINK_NAMES = "\n".join(f"- {name}" for name in REFERENCE_LINKS)


# LLM이 고른 이름을 실제 주소로 변환한다. 목록에 없으면 빈 문자열을 반환한다.
def resolve_reference_link(link_name: str | None) -> str:
    if not link_name:
        return ""

    return REFERENCE_LINKS.get(link_name.strip(), "")


# 창구 이름 목록을 (링크 목록, 목록에 없던 이름들)로 나눈다.
# 목록에 없는 이름은 버리지 않고 돌려주어 웹 검색 단계에서 실제 주소를 찾게 한다.
def resolve_reference_links(
    link_names: list[str] | None,
) -> tuple[list[dict], list[str]]:
    if not link_names:
        return [], []

    links = []
    unmatched = []

    for name in link_names:
        stripped = (name or "").strip()

        if not stripped:
            continue

        url = resolve_reference_link(stripped)

        if url:
            links.append({"title": stripped, "url": url})
        else:
            unmatched.append(stripped)

    return links, unmatched
