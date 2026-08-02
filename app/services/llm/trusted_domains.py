"""
웹 검색으로 찾은 링크 중 신뢰할 수 있는 도메인만 통과시키는 필터.

검색 결과를 그대로 쓰면 LLM이 주소를 지어내는 것과 위험이 비슷해진다.
공식 창구를 안내하는 것이 목적이므로 정부/공공/공식 도메인만 허용한다.
"""

from urllib.parse import urlparse

# 접미사로 판정하는 도메인. 대한민국 공공기관과 해외 정부 기관을 포괄한다.
TRUSTED_SUFFIXES: tuple[str, ...] = (
    ".go.kr",  # 정부 기관
    ".or.kr",  # 공공기관, 협회
    ".re.kr",  # 정부출연연구기관
    ".ac.kr",  # 대학
    ".gov",  # 미국 등 해외 정부
    ".gov.uk",
    ".europa.eu",
)

# 위 규칙으로 못 잡는 개별 도메인
TRUSTED_HOSTS: frozenset[str] = frozenset(
    {
        "dart.fss.or.kr",
        "www.krx.co.kr",  # 한국거래소 (co.kr이라 접미사로 안 잡힌다)
        "krx.co.kr",
        "www.opinet.co.kr",  # 한국석유공사 오피넷
        "opinet.co.kr",
    }
)

# 검색할 때 include_domains로 제한해서 사용하기 위한 도메인 목록
TRUSTED_DOMAINS = [
    "go.kr",
    "or.kr",
    "re.kr",
    "ac.kr",
    "gov",
    "gov.uk",
    "europa.eu",
    "krx.co.kr",
    "opinet.co.kr",
]


def is_trusted_url(url: str | None) -> bool:
    if not url:
        return False

    parsed = urlparse(url)

    # http/https가 아니면 링크로 쓰지 않는다 (javascript:, data: 등 차단)
    if parsed.scheme not in ("http", "https"):
        return False

    host = (parsed.hostname or "").lower()

    if not host:
        return False

    if host in TRUSTED_HOSTS:
        return True

    return host.endswith(TRUSTED_SUFFIXES)
