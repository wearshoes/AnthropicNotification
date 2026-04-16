"""Fetch page metadata (og:title, og:description, og:image) for URL enrichment."""

import logging
import re
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)

GENERIC_DESCRIPTIONS = {
    "anthropic is an ai safety",
}


def _parse_meta(html: str) -> dict[str, str | None]:
    """Extract og:title, og:description, og:image and <title> from HTML."""
    og = {}
    for m in re.finditer(r'<meta\s+[^>]*?property=["\']og:(\w+)["\'][^>]*?content=["\']([^"\']*)["\']', html, re.I):
        og[m.group(1)] = m.group(2)
    for m in re.finditer(r'<meta\s+[^>]*?content=["\']([^"\']*)["\'][^>]*?property=["\']og:(\w+)["\']', html, re.I):
        og[m.group(2)] = m.group(1)

    title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.DOTALL)
    page_title = title_match.group(1).strip() if title_match else None

    return {
        "og_title": og.get("title"),
        "og_description": og.get("description"),
        "og_image": og.get("image"),
        "page_title": page_title,
    }


def _is_generic_description(desc: str | None) -> bool:
    """Check if description is a generic company boilerplate."""
    if not desc:
        return True
    lower = desc.lower().strip()
    return any(lower.startswith(g) for g in GENERIC_DESCRIPTIONS)


def enrich_url(url: str) -> dict:
    """Fetch a URL and extract metadata. Falls back to slug on failure."""
    slug = urlparse(url).path.rstrip("/").split("/")[-1]

    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        response.raise_for_status()
        meta = _parse_meta(response.text[:30000])

        title = meta["og_title"] or meta["page_title"] or slug
        description = meta["og_description"] if not _is_generic_description(meta["og_description"]) else None
        image = meta["og_image"]

        return {"url": url, "title": title, "description": description, "image": image}

    except Exception as e:
        logger.warning(f"Failed to enrich {url}: {e}")
        return {"url": url, "title": slug, "description": None, "image": None}


def enrich_urls(changes: dict[str, set[str]]) -> dict[str, list[dict]]:
    """Enrich all URLs in changes dict. Returns dict[category, list[enriched_dict]]."""
    result = {}
    for category, urls in changes.items():
        result[category] = [enrich_url(url) for url in sorted(urls)]
    return result
