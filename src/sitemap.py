"""Fetch and parse Anthropic sitemap.xml, accepting only trusted content URLs."""

from __future__ import annotations

from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup
from lxml import etree


ANTHROPIC_HOST = "www.anthropic.com"
ACADEMY_HOST = "academy.claude.com"
TRUSTED_HOSTS = frozenset({ANTHROPIC_HOST, ACADEMY_HOST})
SITEMAP_URL = f"https://{ANTHROPIC_HOST}/sitemap.xml"
ACADEMY_SITEMAP_URL = f"https://{ACADEMY_HOST}/sitemap.xml"
SITEMAP_URLS = (SITEMAP_URL, ACADEMY_SITEMAP_URL)
ENGINEERING_INDEX_URL = f"https://{ANTHROPIC_HOST}/engineering"
SITEMAP_NS = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
TRUSTED_SCHEME = "https"
MAX_REDIRECTS = 5
MAX_URL_CHARS = 2_048
MIN_TOTAL_CONTENT_URLS = 300
CATEGORIES = {
    "news": (ANTHROPIC_HOST, "/news/"),
    "research": (ANTHROPIC_HOST, "/research/"),
    "engineering": (ANTHROPIC_HOST, "/engineering/"),
    "learn": (ACADEMY_HOST, "/collections/"),
}
NEWS_SECTION_PATHS = frozenset({
    "/news/announcements",
    "/news/features",
    "/news/models",
    "/news/partnerships",
    "/news/policy",
    "/news/product",
    "/news/safeguards",
    "/news/security",
})


class UntrustedUrlError(ValueError):
    """Raised when a fetch target leaves the exact Anthropic origin."""


class IncompleteSitemapError(RuntimeError):
    """Raised when a sitemap is too small to seed or process safely."""


def canonicalize_url(url: str) -> str:
    """Validate the exact HTTPS origin and strip query/fragment noise."""
    if not isinstance(url, str) or len(url) > MAX_URL_CHARS:
        raise UntrustedUrlError("URL is missing or exceeds the accepted length")
    parsed = urlparse(url)
    if (
        parsed.scheme.lower() != TRUSTED_SCHEME
        or parsed.hostname not in TRUSTED_HOSTS
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port is not None
        or parsed.netloc != parsed.hostname
    ):
        raise UntrustedUrlError("URL is outside the trusted content origins")
    return urlunparse(
        (TRUSTED_SCHEME, parsed.hostname, parsed.path or "/", "", "", "")
    )


def _status_code(response) -> int:
    status = getattr(response, "status_code", 200)
    return status if isinstance(status, int) else 200


def _get_without_untrusted_redirects(url: str):
    current = canonicalize_url(url)
    headers = {"User-Agent": "Mozilla/5.0 (compatible; AnthropicNotification/1.0)"}
    for _ in range(MAX_REDIRECTS + 1):
        response = requests.get(
            current,
            headers=headers,
            timeout=30,
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
    raise requests.exceptions.TooManyRedirects("too many sitemap redirects")


def fetch_sitemap(url: str = SITEMAP_URL) -> list[dict]:
    """Fetch sitemap XML after validating every redirect target."""
    response = _get_without_untrusted_redirects(url)
    parser = etree.XMLParser(resolve_entities=False, no_network=True)
    root = etree.fromstring(response.content, parser=parser)
    entries = []
    for url_elem in root.findall("ns:url", SITEMAP_NS):
        loc_elem = url_elem.find("ns:loc", SITEMAP_NS)
        if loc_elem is None or not loc_elem.text:
            continue
        lastmod_elem = url_elem.find("ns:lastmod", SITEMAP_NS)
        entries.append({
            "loc": loc_elem.text.strip(),
            "lastmod": lastmod_elem.text.strip()
            if lastmod_elem is not None and lastmod_elem.text
            else None,
        })
    return entries


def fetch_sitemaps(urls: tuple[str, ...] = SITEMAP_URLS) -> list[dict]:
    """Fetch every configured sitemap as one fail-closed snapshot."""
    entries = []
    for url in urls:
        entries.extend(fetch_sitemap(url))
    return entries


def _is_single_segment_path(path: str, prefix: str) -> bool:
    normalized = path.rstrip("/")
    if not normalized.startswith(prefix):
        return False
    remainder = normalized[len(prefix):]
    return bool(remainder) and "/" not in remainder


def fetch_engineering_urls(url: str = ENGINEERING_INDEX_URL) -> set[str]:
    """Extract trusted article links from Anthropic's engineering landing page."""
    response = _get_without_untrusted_redirects(url)
    soup = BeautifulSoup(response.text, "html.parser")
    content = soup.find("main")
    if content is None:
        return set()
    urls = set()
    for anchor in content.find_all("a", href=True):
        try:
            canonical = canonicalize_url(urljoin(url, anchor["href"]))
        except (TypeError, ValueError):
            continue
        parsed = urlparse(canonical)
        if (
            parsed.hostname == ANTHROPIC_HOST
            and _is_single_segment_path(parsed.path, "/research/")
        ):
            urls.add(canonical)
    return urls


def filter_by_category(
    entries: list[dict],
    engineering_urls: set[str] | None = None,
) -> dict[str, set[str]]:
    """Group trusted canonical content URLs by configured path prefix."""
    result = {category: set() for category in CATEGORIES}
    sitemap_urls = set()
    for entry in entries:
        try:
            canonical = canonicalize_url(entry["loc"])
        except (KeyError, TypeError, ValueError):
            continue
        sitemap_urls.add(canonical)
        parsed = urlparse(canonical)
        for category, (host, prefix) in CATEGORIES.items():
            if (
                parsed.hostname == host
                and _is_single_segment_path(parsed.path, prefix)
                and not (
                    category == "news"
                    and parsed.path.rstrip("/") in NEWS_SECTION_PATHS
                )
            ):
                result[category].add(canonical)
                break

    for url in engineering_urls or set():
        try:
            canonical = canonicalize_url(url)
        except (TypeError, ValueError):
            continue
        parsed = urlparse(canonical)
        if (
            canonical in sitemap_urls
            and parsed.hostname == ANTHROPIC_HOST
            and _is_single_segment_path(parsed.path, "/research/")
        ):
            result["research"].discard(canonical)
            result["engineering"].add(canonical)
    return result


def validate_snapshot_shape(categorized: dict[str, set[str]]) -> None:
    """Reject empty categories and grossly partial HTTP-200 sitemap snapshots."""
    missing_or_empty = [
        category for category in CATEGORIES
        if not categorized.get(category)
    ]
    total = sum(len(categorized.get(category, set())) for category in CATEGORIES)
    if missing_or_empty or total < MIN_TOTAL_CONTENT_URLS:
        raise IncompleteSitemapError(
            f"Sitemap snapshot is incomplete: total={total}, "
            f"empty={','.join(missing_or_empty) or 'none'}"
        )
