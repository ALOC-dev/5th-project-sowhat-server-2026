"""
구조:
    1. 상수 정의     - RSS URL 목록, HTTP 헤더
    2. 본문 크롤러   - fetch_yonhap_body()
    3. RSS 처리기    - process_yonhap_rss()
    4. 전체 실행기   - run_yonhap_crawling()
"""

import asyncio
import aiohttp
import feedparser
from bs4 import BeautifulSoup

from app.crud.article import create_article

# 수집 대상 RSS 피드 목록
YONHAP_RSS: dict[str, str] = {
    "연합뉴스(전체)": "https://www.yna.co.kr/rss/news.xml",
    "연합뉴스(산업/IT)": "https://www.yna.co.kr/rss/industry.xml",
}

REQUEST_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# 테스트 시 수집할 기사 수 (실서비스에선 ?)
MAX_ARTICLES_PER_FEED: int | None = 5

# 연합뉴스 본문 CSS selector 우선순위 목록
YONHAP_BODY_SELECTORS: list[str] = [
    ".story-news.article",
    ".story-news",
    "#articleWrap",
    "#newsWriterArea",
]

# 본문에서 제거할 불필요한 태그 selector
REMOVE_SELECTORS: list[str] = [
    "script",
    "style",
    ".comp-box",
    ".photo-group",
]


# paragraph crawler


async def fetch_yonhap_body(
    session: aiohttp.ClientSession,
    article_url: str,
) -> str:
    """
    연합뉴스 기사 URL에서 본문 텍스트를 추출한다.

    Args:
        session:     재사용할 aiohttp 세션
        article_url: 크롤링할 기사 URL

    Returns:
        본문 텍스트 (실패 시 빈 문자열 "")
    """
    try:
        async with session.get(article_url, headers=REQUEST_HEADERS) as response:

            # 정상 응답이 아니면 빠르게 종료
            if response.status != 200:
                print(f"[HTTP {response.status}] 접근 실패: {article_url}")
                return ""

            html = await response.text()

        # --- HTML 파싱 ---
        soup = BeautifulSoup(html, "html.parser")

        # 우선순위 순으로 본문 selector 시도
        body_tag = None
        for selector in YONHAP_BODY_SELECTORS:
            body_tag = soup.select_one(selector)
            if body_tag:
                break

        if body_tag is None:
            print(f"[WARN] 본문 selector 매칭 실패: {article_url}")
            return ""

        # 광고·스크립트 등 불필요한 태그 제거
        for tag in body_tag.select(", ".join(REMOVE_SELECTORS)):
            tag.decompose()

        # <p> 태그 단위로 텍스트 추출 후 줄바꿈으로 합치기
        paragraphs = [p.get_text(strip=True) for p in body_tag.select("p")]
        return "\n".join(paragraphs)

    except Exception as exc:
        print(f"[ERROR] 본문 크롤링 예외: {exc} / URL: {article_url}")
        return ""


# RSS Process


async def fetch_rss_entries(rss_url: str) -> list:
    """
    RSS URL을 비동기로 요청하고 feedparser로 파싱한 entry 목록을 반환한다.

    별도 함수로 분리한 이유:
        - requests(동기)를 async 함수 내부에서 쓰면 이벤트 루프를 블로킹함
        - aiohttp로 통일해서 테스트 mock도 aioresponses 하나로 처리 가능

    Returns:
        feed.entries 리스트 (실패 시 빈 리스트)
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                rss_url,
                headers=REQUEST_HEADERS,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status != 200:
                    print(f"[HTTP {response.status}] RSS 요청 실패: {rss_url}")
                    return []
                raw = await response.read()  # bytes 그대로 받기

        feed = feedparser.parse(raw)

        if feed.bozo:
            print(f"[WARN] RSS 파싱 경고: {feed.get('bozo_exception')}")

        return feed.entries

    except Exception as exc:
        print(f"[ERROR] RSS 요청 예외: {exc}")
        return []


async def process_yonhap_rss(
    category_name: str,
    rss_url: str,
    max_articles: int | None = MAX_ARTICLES_PER_FEED,
) -> list[dict]:
    """
    하나의 RSS 피드를 처리해 기사 제목·링크·본문을 수집한다.

    Args:
        category_name: 로그용 카테고리 이름 (예: "연합뉴스(전체)")
        rss_url:       RSS 피드 URL
        max_articles:  수집할 최대 기사 수 (None이면 전체)

    Returns:
        수집된 기사 딕셔너리 목록
        [{"title": ..., "link": ..., "content": ..., "media": "연합뉴스"}, ...]
    """
    print("=" * 60)
    print(f"[START] {category_name} RSS 수집 시작")

    entries = await fetch_rss_entries(rss_url)

    if not entries:
        print(f"[SKIP]  {category_name} - 수집된 기사 없음")
        return []

    # max_articles가 None이면 전체, 숫자면 슬라이싱
    target_entries = entries[:max_articles] if max_articles else entries
    print(f"[INFO]  처리 대상 기사 수: {len(target_entries)}")

    results: list[dict] = []

    async with aiohttp.ClientSession() as session:
        for entry in target_entries:
            title = entry.get("title", "")
            link = entry.get("link", "")

            print("-" * 60)
            print(f"[기사] {title}")
            print(f"[URL]  {link}")

            # DB 중복 검사 (DB 연결 후 주석 해제)
            # if crud_article.get_article_by_link(db, link=link):
            #     print("[SKIP] 이미 저장된 기사")
            #     continue

            content = await fetch_yonhap_body(session, link)

            if content:
                print(f"[OK]   본문 {len(content)}자 수집 완료")
                print(content[:200])

                results.append(
                    {
                        "title": title,
                        "link": link,
                        "content": content,
                        "media": "연합뉴스",
                    }
                )

            else:
                print("[FAIL] 본문 수집 실패")

            # 서버 부하 방지용 딜레이
            await asyncio.sleep(0.5)

    print(f"[DONE]  {category_name} 수집 완료 - {len(results)}건")
    return results


# 전체 실


async def run_yonhap_crawling() -> dict[str, list[dict]]:
    """
    YONHAP_RSS에 정의된 모든 카테고리를 병렬로 수집한다.

    Returns:
        카테고리 이름을 key, 수집 결과 리스트를 value로 하는 딕셔너리
    """
    print("=" * 60)
    print("[CRAWL] 연합뉴스 전체 RSS 수집 시작")

    tasks = {name: process_yonhap_rss(name, url) for name, url in YONHAP_RSS.items()}

    # asyncio.gather로 모든 카테고리 병렬 실행
    results = await asyncio.gather(*tasks.values())

    return dict(zip(tasks.keys(), results))


# 직접 실행

if __name__ == "__main__":
    asyncio.run(run_yonhap_crawling())
