import asyncio
import requests
import feedparser
import aiohttp
from bs4 import BeautifulSoup

# DB 관련 임포트
# DB 연결 전까지는 주석 유지
# from app.db.database import SessionLocal
# from app.crud import article as crud_article


# 연합뉴스 RSS 목록
YONHAP_RSS = {
    "연합뉴스(전체)": "https://www.yna.co.kr/rss/news.xml",
    "연합뉴스(산업/IT)": "https://www.yna.co.kr/rss/industry.xml"
}


# 브라우저처럼 보이게 하는 헤더
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


async def fetch_yonhap_body(
    session: aiohttp.ClientSession,
    link: str
) -> str:
    """연합뉴스 기사 본문 크롤링"""

    try:
        async with session.get(
            link,
            headers=HEADERS
        ) as response:

            # 요청 실패
            if response.status != 200:
                print(f"접근 실패 ({response.status}) : {link}")
                return ""

            # HTML 가져오기
            html = await response.text()

            # HTML 파싱
            soup = BeautifulSoup(html, "html.parser")

            # 연합뉴스 본문 selector
            body = (
                soup.select_one(".story-news.article")
                or soup.select_one(".story-news")
                or soup.select_one("#articleWrap")
                or soup.select_one("#newsWriterArea")
            )

            # 본문 못 찾은 경우
            if not body:
                print("본문 selector 실패")
                print(link)
                return ""

            # 불필요한 요소 제거
            for tag in body.select(
                "script, style, .comp-box, .photo-group"
            ):
                tag.decompose()

            # 텍스트 추출
            paragraphs = body.select("p")

            content = "\n".join(
                p.get_text(strip=True)
                for p in paragraphs
            )
            
            return content

    except Exception as e:
        print(f"본문 크롤링 에러: {e}")
        return ""


async def process_yonhap_rss(
    category_name: str,
    rss_url: str
):
    """RSS 읽기 및 기사 처리"""

    print("=" * 60)
    print(f"{category_name} RSS 수집 시작")

    try:
        # RSS 요청
        response = requests.get(
            rss_url,
            headers=HEADERS,
            timeout=10
        )

        # 응답 확인
        print(f"RSS 응답 코드: {response.status_code}")

        # RSS 파싱
        feed = feedparser.parse(response.content)

        # RSS 오류 여부
        print(f"RSS bozo 상태: {feed.bozo}")

        if feed.bozo:
            print(feed.get("bozo_exception"))

        # 기사 개수
        print(f"가져온 기사 수: {len(feed.entries)}")

        # 기사 없으면 종료
        if not feed.entries:
            print("RSS 기사 없음")
            return

        # HTTP 세션 생성
        async with aiohttp.ClientSession() as session:

            # 테스트용으로 5개만 실행
            for entry in feed.entries[:5]:

                title = entry.title
                link = entry.link

                print("-" * 60)
                print(f"기사 제목: {title}")
                print(f"기사 링크: {link}")

                # -------------------------
                # DB 중복 검사 임시 비활성화
                # -------------------------

                # existing_article = crud_article.get_article_by_link(
                #     db,
                #     link=link
                # )

                # if existing_article:
                #     print("이미 저장된 기사")
                #     continue

                # 본문 크롤링
                content = await fetch_yonhap_body(
                    session,
                    link
                )

                # 본문 출력
                if content:

                    print("본문 크롤링 성공")
                    print(content[:300])

                    # -------------------------
                    # DB 저장 임시 비활성화
                    # -------------------------

                    # crud_article.create_article(
                    #     db=db,
                    #     title=title,
                    #     link=link,
                    #     content=content,
                    #     media="연합뉴스"
                    # )

                else:
                    print("본문 크롤링 실패")

                # 서버 부하 방지
                await asyncio.sleep(0.5)

    except Exception as e:
        print(f"RSS 처리 에러: {e}")


async def run_yonhap_crawling():
    """전체 RSS 병렬 실행"""

    print("연합뉴스 RSS 수집 시작")

    tasks = [
        process_yonhap_rss(name, url)
        for name, url in YONHAP_RSS.items()
    ]

    await asyncio.gather(*tasks)


# 직접 실행
if __name__ == "__main__":
    asyncio.run(run_yonhap_crawling())
