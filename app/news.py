"""Fetch real headlines from RSS feeds to use as article topics."""

import random
import xml.etree.ElementTree as ET
from urllib.request import urlopen, Request
from urllib.error import URLError

RSS_FEEDS = [
    "https://feeds.arstechnica.com/arstechnica/technology-lab",
    "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://feeds.feedburner.com/venturebeat/SZYF",
    "https://www.wired.com/feed/tag/ai/latest/rss",
]

FALLBACK_TOPICS = [
    "A breakthrough in multi-agent coordination",
    "New techniques for LLM reasoning and chain-of-thought",
    "The latest in AI policy and governance frameworks",
    "Advances in autonomous AI systems",
    "How AI is transforming scientific discovery",
]


def _parse_rss(xml_text: str) -> list[str]:
    """Extract titles from RSS/Atom XML."""
    titles = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return titles

    # Standard RSS
    for item in root.iter("item"):
        title_el = item.find("title")
        if title_el is not None and title_el.text:
            titles.append(title_el.text.strip())

    # Atom feeds
    if not titles:
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.findall(".//atom:entry", ns):
            title_el = entry.find("atom:title", ns)
            if title_el is not None and title_el.text:
                titles.append(title_el.text.strip())

    return titles


def fetch_headlines(count: int = 10) -> list[str]:
    """Fetch recent headlines from RSS feeds. Falls back to static topics on failure."""
    all_titles: list[str] = []
    feeds = random.sample(RSS_FEEDS, min(3, len(RSS_FEEDS)))

    for url in feeds:
        try:
            req = Request(url, headers={"User-Agent": "NeuralGazette/1.0"})
            with urlopen(req, timeout=10) as resp:
                xml_text = resp.read().decode("utf-8", errors="replace")
            all_titles.extend(_parse_rss(xml_text))
        except (URLError, OSError):
            continue

    if len(all_titles) < count:
        all_titles.extend(FALLBACK_TOPICS)

    random.shuffle(all_titles)
    return all_titles[:count]
