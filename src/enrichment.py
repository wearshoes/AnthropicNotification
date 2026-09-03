"""Fetch page metadata while preventing redirects outside trusted origins."""

from __future__ import annotations

import logging
import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from src.sitemap import canonicalize_url


logger = logging.getLogger(__name__)
MAX_REDIRECTS = 5
GENERIC_DESCRIPTIONS = {
    "Anthropic is an AI safety and research company that's working to build reliable, interpretable, and steerable AI systems.",
}


def _slug_title(url: str) -> str:
    return urlparse(url).path.rstrip("/").split("/")[-1] or url


def _status_code(response) -> int:
    status = getattr(response, "status_code", 200)
    return status if isinstance(status, int) else 200


def _get_trusted_page(url: str):
    current = canonicalize_url(url)
    headers = {"User-Agent": "Mozilla/5.0 (compatible; AnthropicNotification/1.0)"}
    for _ in range(MAX_REDIRECTS + 1):
        response = requests.get(
            current,
            headers=headers,
            timeout=15,
            allow_redirects=False,
        )
        status = _status_code(response)
        if status not in (301, 302, 303, 307, 308):
            response.raise_for_status()
            return response
        location = response.headers.get("Location")
        if not location:
            raise requests.exceptions.TooManyRedirects("redirect response has no Location")
        current = canonicalize_url(urljoin(current, location))
    raise requests.exceptions.TooManyRedirects("too many page redirects")


def _meta_content(soup: BeautifulSoup, property_name: str) -> str | None:
    element = soup.find("meta", attrs={"property": property_name})
    if not element:
        return None
    value = element.get("content")
    return value.strip() if isinstance(value, str) and value.strip() else None


def enrich_url(url: str) -> dict:
    """Return a stable metadata snapshot, falling back to the URL slug."""
    fallback = {
        "url": url,
        "title": _slug_title(url),
        "description": None,
        "image": None,
    }
    try:
        response = _get_trusted_page(url)
        soup = BeautifulSoup(response.text, "lxml")
        title = _meta_content(soup, "og:title")
        if not title and soup.title and soup.title.string:
            title = re.sub(r"\s*\|\s*Anthropic\s*$", "", soup.title.string.strip())
        description = _meta_content(soup, "og:description")
        if description in GENERIC_DESCRIPTIONS:
            description = None
        return {
            "url": url,
            "title": title or fallback["title"],
            "description": description,
            "image": _meta_content(soup, "og:image"),
        }
    except Exception as exc:
        logger.warning("Failed to enrich %s: %s", url, exc)
        return fallback


def enrich_urls(changes: dict[str, set[str]]) -> dict[str, list[dict]]:
    """Enrich every URL in deterministic category and URL order."""
    return {
        category: [enrich_url(url) for url in sorted(urls)]
        for category, urls in sorted(changes.items())
    }
