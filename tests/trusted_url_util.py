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

# 검색할 때 include_domains로 제한해서 사용하기 위한 도메인 목록
TRUSTED_DOMAINS = [
    "go.kr",
    "or.kr",
    "re.kr",
    "ac.kr",
    "gov",
    "gov.uk",
    "europa.eu",
]

from app.services.search.trusted_links import TRUSTED_HOSTS


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

    if host in TRUSTED_HOSTS.values():
        return True

    return host.endswith(TRUSTED_SUFFIXES)
