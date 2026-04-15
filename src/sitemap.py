"""Fetch and parse Anthropic sitemap.xml, filter URLs by category."""

from urllib.parse import urlparse

import requests
from lxml import etree

SITEMAP_URL = "https://www.anthropic.com/sitemap.xml"
SITEMAP_NS = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}

CATEGORIES = {
    "news": "/news/",
    "research": "/research/",
    "engineering": "/engineering/",
    "learn": "/learn/",
}


def fetch_sitemap(url: str = SITEMAP_URL) -> list[dict]:
    """Fetch sitemap.xml and return list of {loc, lastmod} entries."""
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (compatible; AnthropicNotification/1.0)"}, timeout=30)
    response.raise_for_status()

    root = etree.fromstring(response.content)
    entries = []
    for url_elem in root.findall("ns:url", SITEMAP_NS):
        loc_elem = url_elem.find("ns:loc", SITEMAP_NS)
        lastmod_elem = url_elem.find("ns:lastmod", SITEMAP_NS)
        if loc_elem is not None and loc_elem.text:
            entries.append({
                "loc": loc_elem.text.strip(),
                "lastmod": lastmod_elem.text.strip() if lastmod_elem is not None and lastmod_elem.text else None,
            })
    return entries


def filter_by_category(entries: list[dict]) -> dict[str, set[str]]:
    """Group sitemap URLs by category. Only includes URLs with a slug after the category prefix."""
    result = {cat: set() for cat in CATEGORIES}

    for entry in entries:
        path = urlparse(entry["loc"]).path
        for category, prefix in CATEGORIES.items():
            if path.startswith(prefix) and len(path) > len(prefix):
                result[category].add(entry["loc"])
                break

    return result
