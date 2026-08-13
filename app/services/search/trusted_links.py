"""
웹 검색으로 찾은 링크 중 신뢰할 수 있는 도메인만 통과시키는 필터.

검색 결과를 그대로 쓰면 LLM이 주소를 지어내는 것과 위험이 비슷해진다.
공식 창구를 안내하는 것이 목적이므로 정부/공공/공식 도메인만 허용한다.
"""

# 개인해설의 조회/신청 링크로 사용할 공식 창구 목록(화이트리스트)
TRUSTED_HOSTS: dict[str, str] = {
    "금융감독원 전자공시시스템": "dart.fss.or.kr",
    "한국거래소": "www.krx.co.kr",
    "미국 증권거래위원회 전자공시시스템": "www.sec.gov",
    "K-Sight 무역보험 빅데이터 플랫폼": "ksight.ksure.or.kr",
    "한국석유공사 페트로넷": "www.petronet.co.kr",
    "한국석유공사 오피넷": "www.opinet.co.kr",
    "한국은행 경제통계시스템": "ecos.bok.or.kr",
    "국가통계포털": "kosis.kr",
    "국가데이터처": "mods.go.kr",
    "고용24": "www.work24.go.kr",
    "정부24": "www.gov.kr",
    "국세청 홈택스": "hometax.go.kr",
    "국민건강보험공단": "www.nhis.or.kr",
    "국민연금공단": "www.nps.or.kr",
    "법제처 국가법령정보센터": "www.law.go.kr",
    "행정안전부": "www.mois.go.kr",
    "재정경제부": "www.moef.go.kr",
    "고용노동부": "www.moel.go.kr",
    "보건복지부": "www.mohw.go.kr",
    "교육부": "www.moe.go.kr",
    "국토교통부": "www.molit.go.kr",
    "산업통상자원부": "www.motir.go.kr",
    "과학기술정보통신부": "www.msit.go.kr",
    "환경부": "www.me.go.kr",
    "중소벤처기업부": "www.mss.go.kr",
    "금융위원회": "www.fsc.go.kr",
    "공정거래위원회": "www.ftc.go.kr",
    "질병관리청": "www.kdca.go.kr",
    "기상청": "www.weather.go.kr",
    "한국소비자원": "www.kca.go.kr",
    "근로복지공단": "www.comwel.or.kr",
    "한국주택금융공사": "www.hf.go.kr",
    "한국토지주택공사": "www.lh.or.kr",
    "대한법률구조공단": "www.klac.or.kr",
    "국민권익위원회": "www.acrc.go.kr",
}

# 검색할 때 include_domains로 제한해서 사용하기 위한 도메인 목록
TRUSTED_DOMAINS = [
    "go.kr",
    "or.kr",
    "re.kr",
    "ac.kr",
    "gov",
    "gov.uk",
    "europa.eu",
    # "gov.kr",
    # "kosis.kr",
    # "krx.co.kr",
    # "opinet.co.kr",
    # "petronet.co.kr",
]

TRUSTED_LINK_NAMES = "\n".join(TRUSTED_HOSTS.keys())
