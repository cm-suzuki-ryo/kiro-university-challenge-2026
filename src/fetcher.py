"""RSS フィード取得とパース"""
import logging
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from html import unescape
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

RSS_URL = "https://aws.amazon.com/about-aws/whats-new/recent/feed/"
USER_AGENT = "aws-whatsnew-notifier/1.0"
FETCH_TIMEOUT = 30


@dataclass
class FeedItem:
    guid: str
    title: str
    description_plain: str
    description_html: str
    pub_date: str
    category: str
    link: str
    service_category: str = "uncategorized"


def fetch_rss(url: str = RSS_URL, timeout: int = FETCH_TIMEOUT) -> str:
    """RSS フィードの XML テキストを取得して返す"""
    req = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(req, timeout=timeout) as resp:
            content = resp.read().decode("utf-8")
            logger.debug("Fetched RSS feed: %d bytes", len(content))
            return content
    except (URLError, HTTPError) as e:
        logger.error("Failed to fetch RSS feed: %s", e)
        raise


def parse_rss(xml_text: str) -> list[FeedItem]:
    """RSS XML をパースして FeedItem のリストを返す"""
    root = ET.fromstring(xml_text)
    items: list[FeedItem] = []

    for item in root.findall(".//item"):
        guid = item.findtext("guid", "")
        title = item.findtext("title", "").strip()
        description_html = item.findtext("description", "")
        pub_date = item.findtext("pubDate", "")
        category = item.findtext("category", "")
        link = item.findtext("link", "")

        description_plain = re.sub(r"<[^>]+>", "", unescape(description_html)).strip()

        items.append(
            FeedItem(
                guid=guid,
                title=title,
                description_plain=description_plain,
                description_html=description_html,
                pub_date=pub_date,
                category=category,
                link=link,
            )
        )

    logger.info("Parsed %d items from RSS feed", len(items))
    return items
