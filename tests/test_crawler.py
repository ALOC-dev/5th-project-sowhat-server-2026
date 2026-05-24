import pytest
import aiohttp
from unittest.mock import MagicMock, patch
from aioresponses import aioresponses

from app.services.schedule import (
    fetch_yonhap_body,
    fetch_rss_entries,
    process_yonhap_rss,
    YONHAP_BODY_SELECTORS,
)


@pytest.fixture
def valid_article_html() -> str:
    return """
    <html><body>
        <div class="story-news article">
            <p>첫 번째 문단입니다.</p>
            <p>두 번째 문단입니다.</p>
            <script>console.log('remove this')</script>
            <div class="comp-box">remove this</div>
        </div>
    </body></html>
    """


@pytest.fixture
def valid_rss_xml() -> bytes:
    return b"""<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
        <channel>
            <title>Yonhap News</title>
            <item>
                <title>Test Article 1</title>
                <link>https://www.yna.co.kr/article/1</link>
            </item>
            <item>
                <title>Test Article 2</title>
                <link>https://www.yna.co.kr/article/2</link>
            </item>
        </channel>
    </rss>"""


@pytest.fixture
def empty_rss_xml() -> bytes:
    return b"""<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
        <channel><title>Empty Feed</title></channel>
    </rss>"""


class TestFetchYonhapBody:

    async def test_정상_본문_추출(self, valid_article_html):
        with aioresponses() as mock:
            mock.get(
                "https://www.yna.co.kr/article/1", status=200, body=valid_article_html
            )
            async with aiohttp.ClientSession() as session:
                result = await fetch_yonhap_body(
                    session, "https://www.yna.co.kr/article/1"
                )

        assert "첫 번째 문단입니다." in result
        assert "두 번째 문단입니다." in result

    async def test_스크립트_광고_제거(self, valid_article_html):
        with aioresponses() as mock:
            mock.get(
                "https://www.yna.co.kr/article/1", status=200, body=valid_article_html
            )
            async with aiohttp.ClientSession() as session:
                result = await fetch_yonhap_body(
                    session, "https://www.yna.co.kr/article/1"
                )

        assert "remove this" not in result

    async def test_404_응답시_빈문자열_반환(self):
        with aioresponses() as mock:
            mock.get("https://www.yna.co.kr/article/404", status=404)
            async with aiohttp.ClientSession() as session:
                result = await fetch_yonhap_body(
                    session, "https://www.yna.co.kr/article/404"
                )

        assert result == ""

    async def test_500_응답시_빈문자열_반환(self):
        with aioresponses() as mock:
            mock.get("https://www.yna.co.kr/article/500", status=500)
            async with aiohttp.ClientSession() as session:
                result = await fetch_yonhap_body(
                    session, "https://www.yna.co.kr/article/500"
                )

        assert result == ""

    async def test_selector_없을때_빈문자열_반환(self):
        unmatched_html = "<html><body><div class='unknown'>내용</div></body></html>"
        with aioresponses() as mock:
            mock.get(
                "https://www.yna.co.kr/article/no-selector",
                status=200,
                body=unmatched_html,
            )
            async with aiohttp.ClientSession() as session:
                result = await fetch_yonhap_body(
                    session, "https://www.yna.co.kr/article/no-selector"
                )

        assert result == ""

    async def test_p태그_없으면_빈문자열_반환(self):
        html_without_p = """
        <div class="story-news article">
            <span>p 태그가 아닌 텍스트</span>
        </div>
        """
        with aioresponses() as mock:
            mock.get(
                "https://www.yna.co.kr/article/no-p", status=200, body=html_without_p
            )
            async with aiohttp.ClientSession() as session:
                result = await fetch_yonhap_body(
                    session, "https://www.yna.co.kr/article/no-p"
                )

        assert result == ""

    async def test_네트워크_예외시_빈문자열_반환(self):
        with aioresponses() as mock:
            mock.get(
                "https://www.yna.co.kr/article/error",
                exception=aiohttp.ClientConnectionError("연결 실패"),
            )
            async with aiohttp.ClientSession() as session:
                result = await fetch_yonhap_body(
                    session, "https://www.yna.co.kr/article/error"
                )

        assert result == ""

    @pytest.mark.parametrize("selector", YONHAP_BODY_SELECTORS)
    async def test_모든_selector_인식(self, selector):
        if selector.startswith("#"):
            tag_html = f'<div id="{selector[1:]}"><p>본문 내용</p></div>'
        else:
            classes = selector.lstrip(".").replace(".", " ")
            tag_html = f'<div class="{classes}"><p>본문 내용</p></div>'

        html = f"<html><body>{tag_html}</body></html>"

        with aioresponses() as mock:
            mock.get(
                "https://www.yna.co.kr/article/selector-test", status=200, body=html
            )
            async with aiohttp.ClientSession() as session:
                result = await fetch_yonhap_body(
                    session, "https://www.yna.co.kr/article/selector-test"
                )

        assert "본문 내용" in result


class TestFetchRssEntries:

    async def test_정상_RSS_파싱(self, valid_rss_xml):
        with aioresponses() as mock:
            mock.get("https://fake-rss.com/feed.xml", status=200, body=valid_rss_xml)
            entries = await fetch_rss_entries("https://fake-rss.com/feed.xml")

        assert len(entries) == 2
        assert entries[0].title == "Test Article 1"
        assert entries[1].title == "Test Article 2"

    async def test_빈_RSS_빈_리스트_반환(self, empty_rss_xml):
        with aioresponses() as mock:
            mock.get("https://fake-rss.com/empty.xml", status=200, body=empty_rss_xml)
            entries = await fetch_rss_entries("https://fake-rss.com/empty.xml")

        assert entries == []

    async def test_RSS_요청_실패시_빈_리스트_반환(self):
        with aioresponses() as mock:
            mock.get("https://fake-rss.com/fail.xml", status=503)
            entries = await fetch_rss_entries("https://fake-rss.com/fail.xml")

        assert entries == []

    async def test_네트워크_예외시_빈_리스트_반환(self):
        with aioresponses() as mock:
            mock.get(
                "https://fake-rss.com/error.xml",
                exception=aiohttp.ClientConnectionError("연결 실패"),
            )
            entries = await fetch_rss_entries("https://fake-rss.com/error.xml")

        assert entries == []


class TestProcessYonhapRss:

    async def test_정상_수집(self):
        fake_entries = [
            MagicMock(title="기사1", link="https://www.yna.co.kr/article/1"),
            MagicMock(title="기사2", link="https://www.yna.co.kr/article/2"),
        ]
        with (
            patch("app.services.schedule.fetch_rss_entries", return_value=fake_entries),
            patch(
                "app.services.schedule.fetch_yonhap_body", return_value="본문 텍스트"
            ),
            patch("app.services.schedule.asyncio.sleep"),
        ):
            results = await process_yonhap_rss("테스트", "https://fake.com/rss.xml")

        assert len(results) == 2
        print(results[0]["title"])
        print(results[0]["content"])
        assert results[0]["media"] == "연합뉴스"

    async def test_RSS_비어있으면_빈_리스트_반환(self):
        with patch("app.services.schedule.fetch_rss_entries", return_value=[]):
            results = await process_yonhap_rss("테스트", "https://fake.com/rss.xml")

        assert results == []

    async def test_본문_수집_실패한_기사는_결과에서_제외(self):
        fake_entries = [
            MagicMock(title="성공 기사", link="https://www.yna.co.kr/article/ok"),
            MagicMock(title="실패 기사", link="https://www.yna.co.kr/article/fail"),
        ]
        with (
            patch("app.services.schedule.fetch_rss_entries", return_value=fake_entries),
            patch(
                "app.services.schedule.fetch_yonhap_body",
                side_effect=["본문 텍스트", ""],
            ),
            patch("app.services.schedule.asyncio.sleep"),
        ):
            results = await process_yonhap_rss("테스트", "https://fake.com/rss.xml")

        assert len(results) == 1
        print(results[0]["title"])

    async def test_max_articles_제한(self):
        fake_entries = [
            MagicMock(title=f"기사{i}", link=f"https://www.yna.co.kr/article/{i}")
            for i in range(5)
        ]
        with (
            patch("app.services.schedule.fetch_rss_entries", return_value=fake_entries),
            patch("app.services.schedule.fetch_yonhap_body", return_value="본문"),
            patch("app.services.schedule.asyncio.sleep"),
        ):
            results = await process_yonhap_rss(
                "테스트", "https://fake.com/rss.xml", max_articles=2
            )

        assert len(results) == 2

    async def test_max_articles_none이면_전체_처리(self):
        fake_entries = [
            MagicMock(title=f"기사{i}", link=f"https://www.yna.co.kr/article/{i}")
            for i in range(10)
        ]
        with (
            patch("app.services.schedule.fetch_rss_entries", return_value=fake_entries),
            patch("app.services.schedule.fetch_yonhap_body", return_value="본문"),
            patch("app.services.schedule.asyncio.sleep"),
        ):
            results = await process_yonhap_rss(
                "테스트", "https://fake.com/rss.xml", max_articles=None
            )

        assert len(results) == 10
