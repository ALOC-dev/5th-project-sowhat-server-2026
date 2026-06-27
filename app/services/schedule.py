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
import time
from datetime import datetime

import app.crud.article as article_crud
from app.exceptions.infrastructure import DatabaseError, ExternalAPIError
from app.db.database import SessionLocal
from app.models.enums import CategoryEnum
from app.services.llm_service import generate_common_analysis


# 수집 대상 RSS 피드 목록
YONHAP_RSS: dict[str, str] = {
    # "연합뉴스(전체)": "https://www.yna.co.kr/rss/news.xml",
    "연합뉴스(산업/IT)": "https://www.yna.co.kr/rss/industry.xml",
    "연합뉴스(정치)": "https://www.yna.co.kr/rss/politics.xml",
    "연합뉴스(경제)": "https://www.yna.co.kr/rss/economy.xml",
    "연합뉴스(사회)": "https://www.yna.co.kr/rss/society.xml",
    "연합뉴스(세계)": "https://www.yna.co.kr/rss/international.xml",
    # "연합뉴스(문화)": "https://www.yna.co.kr/rss/culture.xml",
    # "연합뉴스(스포츠)": "https://www.yna.co.kr/rss/sports.xml",
    # "연합뉴스(연예)": "https://www.yna.co.kr/rss/entertainment.xml",
}


# RSS 이름을 DB CategoryEnum으로 변환
# 현재 CategoryEnum에 POLITICS, ECONOMY, SOCIETY만 있다고 가정
YONHAP_CATEGORY_MAP = {
    "연합뉴스(정치)": CategoryEnum.POLITICS,
    "연합뉴스(경제)": CategoryEnum.ECONOMY,
    "연합뉴스(사회)": CategoryEnum.SOCIETY,

    # CategoryEnum에 INDUSTRY, WORLD가 없으면 임시로 SOCIETY 처리
    "연합뉴스(산업/IT)": CategoryEnum.SOCIETY,
    "연합뉴스(세계)": CategoryEnum.SOCIETY,
}


REQUEST_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# 테스트 시 수집할 기사 수
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


# 날짜 변환 함수
def formatDate(st_time: time.struct_time):
    return datetime(*st_time[:6])


# 본문 크롤링
async def fetch_yonhap_body(
    session: aiohttp.ClientSession,
    article_url: str,
) -> str:
    try:
        async with session.get(article_url, headers=REQUEST_HEADERS) as response:
            if response.status != 200:
                print(f"[HTTP {response.status}] 접근 실패: {article_url}")
                return ""

            html = await response.text()

    except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
        print(f"[ERROR] 본문 요청 실패: {exc} / URL: {article_url}")
        return ""

    soup = BeautifulSoup(html, "html.parser")

    body_tag = None
    for selector in YONHAP_BODY_SELECTORS:
        body_tag = soup.select_one(selector)
        if body_tag:
            break

    if body_tag is None:
        print(f"[WARN] 본문 selector 매칭 실패: {article_url}")
        return ""

    for tag in body_tag.select(", ".join(REMOVE_SELECTORS)):
        tag.decompose()

    paragraphs = [p.get_text(strip=True) for p in body_tag.select("p")]
    return "\n".join(paragraphs)


# RSS 엔트리 파싱
async def fetch_rss_entries(rss_url: str) -> list:
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

                raw = await response.read()

    except Exception as exc:
        raise ExternalAPIError(f"RSS 요청 실패: {exc} / URL: {rss_url}")

    feed = feedparser.parse(raw)

    if feed.bozo:
        print(f"[WARN] RSS 파싱 경고: {feed.get('bozo_exception')}")

    return feed.entries


# 한 카테고리의 RSS 피드 처리
async def process_yonhap_rss(
    category_name: str,
    rss_url: str,
    max_articles: int | None = MAX_ARTICLES_PER_FEED,
) -> list[dict]:

    print("=" * 60)
    print(f"[START] {category_name}: RSS 수집 시작")

    db = SessionLocal()

    try:
        entries = await fetch_rss_entries(rss_url)

        if not entries:
            print(f"[SKIP]  {category_name}: 수집된 기사 없음")
            return []

        target_entries = entries[:max_articles] if max_articles else entries
        print(f"[INFO]  처리 대상 기사 수: {len(target_entries)}")

        results: list[dict] = []

        category = YONHAP_CATEGORY_MAP.get(category_name, CategoryEnum.SOCIETY)

        async with aiohttp.ClientSession() as session:
            for entry in target_entries:
                title = entry.get("title", "")
                source_url = entry.get("link", "")
                published_parsed = entry.get("published_parsed")
                if not published_parsed:
                    print("[SKIP] 발행일자 없음")
                    continue

                published_at = formatDate(published_parsed)
                reporter = entry.get("author", "")

                print("-" * 60)
                print(f"[기사] {title}")
                print(f"[URL]  {source_url}")
                print(f"[발행일자]  {published_at}")
                print(f"[기자]  {reporter}")
                print(f"[카테고리] {category.value}")

                # DB 중복 검사
                if article_crud.get_article_by_source_url(db, source_url):
                    print("[SKIP] 이미 저장된 기사")
                    continue

                content = await fetch_yonhap_body(session, source_url)

                if content:
                    print(f"[OK]   본문 {len(content)}자 수집 완료")

                    try:
                        analysis = await generate_common_analysis(
                            {
                                "title": title,
                                "content": content,
                                "category": category.value,
                            }
                        )
                    except Exception as exc:
                        print(f"[ERROR] 공통 해설 생성 실패: {exc}")

                        analysis = {
                            "summary": "공통 해설 생성 실패",
                            "keyword": "오류",
                        }

                    results.append(
                        {
                            "title": title,
                            "source_url": source_url,
                            "published_at": published_at,
                            "publisher": "연합뉴스",
                            "reporter": reporter,
                            "content": content,
                            "summary": analysis["summary"],
                            "keyword": analysis["keyword"],
                            "category": category,
                        }
                    )
                else:
                    print("[FAIL] 본문 수집 실패")

                await asyncio.sleep(0.5)

        if results:
            print(f"[INFO]  {len(results)}건 기사 수집 완료, DB 저장 시도")
            article_crud.create_articles(db, results)
        else:
            print("[INFO]  저장할 신규 기사 없음")

        return results

    except Exception as exc:
        raise DatabaseError(f"기사 정보 저장 실패: {exc}")

    finally:
        db.close()


# 모든 카테고리에 대해 RSS 피드 수집
async def run_yonhap_crawling() -> dict[str, list[dict]]:
    print("=" * 60)
    print("[CRAWL] 연합뉴스 전체 RSS 수집 시작")

    tasks = {
        name: process_yonhap_rss(name, url)
        for name, url in YONHAP_RSS.items()
    }

    results = await asyncio.gather(*tasks.values(), return_exceptions=True)

    return dict(zip(tasks.keys(), results))


# 주기적 피드 수집 실행기
async def run_yonhap_crawling_periodically(interval_seconds: int = 60) -> None:
    while True:
        started_at = time.monotonic()

        try:
            results = await run_yonhap_crawling()

            for name, res in results.items():
                if isinstance(res, Exception):
                    print(f"[ERROR] {name}: {res}")

        except asyncio.CancelledError:
            raise

        except Exception as exc:
            print(f"[ERROR] 주기 RSS 수집 실패: {exc}")

        elapsed = time.monotonic() - started_at
        await asyncio.sleep(max(0, interval_seconds - elapsed))


# 직접 실행
# if __name__ == "__main__":
#     asyncio.run(run_yonhap_crawling())