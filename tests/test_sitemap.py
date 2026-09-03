"""Tests for src/sitemap.py — written BEFORE implementation."""

import pytest
from unittest.mock import patch, MagicMock

SAMPLE_SITEMAP_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<url>
<loc>https://www.anthropic.com/</loc>
<lastmod>2026-04-15T17:51:06.730Z</lastmod>
</url>
<url>
<loc>https://www.anthropic.com/news/project-glasswing</loc>
<lastmod>2026-04-07T00:00:00.000Z</lastmod>
</url>
<url>
<loc>https://www.anthropic.com/news/claude-sonnet</loc>
<lastmod>2026-02-17T00:00:00.000Z</lastmod>
</url>
<url>
<loc>https://www.anthropic.com/research/constitutional-ai</loc>
<lastmod>2026-03-01T00:00:00.000Z</lastmod>
</url>
<url>
<loc>https://www.anthropic.com/engineering/building-agents</loc>
<lastmod>2026-03-15T00:00:00.000Z</lastmod>
</url>
<url>
<loc>https://academy.claude.com/collections/claude-for-you</loc>
<lastmod>2026-01-10T00:00:00.000Z</lastmod>
</url>
<url>
<loc>https://www.anthropic.com/careers</loc>
<lastmod>2026-04-01T00:00:00.000Z</lastmod>
</url>
</urlset>
"""


class TestFetchSitemap:
    """Tests for fetch_sitemap()."""

    @patch("src.sitemap.requests.get")
    def test_returns_list_of_url_entries(self, mock_get):
        from src.sitemap import fetch_sitemap

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = SAMPLE_SITEMAP_XML.encode()
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        entries = fetch_sitemap()

        assert isinstance(entries, list)
        assert len(entries) == 7
        assert entries[0]["loc"] == "https://www.anthropic.com/"
        assert entries[0]["lastmod"] == "2026-04-15T17:51:06.730Z"

    @patch("src.sitemap.requests.get")
    def test_entry_without_lastmod(self, mock_get):
        from src.sitemap import fetch_sitemap

        xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<url><loc>https://www.anthropic.com/about</loc></url>
</urlset>
"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = xml.encode()
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        entries = fetch_sitemap()

        assert len(entries) == 1
        assert entries[0]["loc"] == "https://www.anthropic.com/about"
        assert entries[0]["lastmod"] is None

    @patch("src.sitemap.requests.get")
    def test_network_error_raises_exception(self, mock_get):
        from src.sitemap import fetch_sitemap
        import requests

        mock_get.side_effect = requests.exceptions.ConnectionError("DNS failed")

        with pytest.raises(Exception):
            fetch_sitemap()

    @patch("src.sitemap.requests.get")
    def test_http_error_raises_exception(self, mock_get):
        from src.sitemap import fetch_sitemap

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")
        mock_get.return_value = mock_response

        with pytest.raises(Exception):
            fetch_sitemap()


class TestFetchSitemaps:
    @patch("src.sitemap.fetch_sitemap")
    def test_combines_every_configured_source(self, mock_fetch):
        from src.sitemap import SITEMAP_URLS, fetch_sitemaps

        mock_fetch.side_effect = [
            [{"loc": "https://www.anthropic.com/news/a", "lastmod": None}],
            [{"loc": "https://academy.claude.com/collections/b", "lastmod": None}],
        ]

        assert fetch_sitemaps() == [
            {"loc": "https://www.anthropic.com/news/a", "lastmod": None},
            {"loc": "https://academy.claude.com/collections/b", "lastmod": None},
        ]
        assert [call.args[0] for call in mock_fetch.call_args_list] == list(SITEMAP_URLS)


class TestFilterByCategory:
    """Tests for filter_by_category()."""

    def _make_entries(self, locs):
        return [{"loc": loc, "lastmod": None} for loc in locs]

    def test_filters_known_categories(self):
        from src.sitemap import filter_by_category

        entries = self._make_entries([
            "https://www.anthropic.com/news/article-1",
            "https://www.anthropic.com/research/paper-1",
            "https://www.anthropic.com/engineering/post-1",
            "https://academy.claude.com/collections/claude-for-you",
        ])

        result = filter_by_category(entries)

        assert result["news"] == {"https://www.anthropic.com/news/article-1"}
        assert result["research"] == {"https://www.anthropic.com/research/paper-1"}
        assert result["engineering"] == {"https://www.anthropic.com/engineering/post-1"}
        assert result["learn"] == {
            "https://academy.claude.com/collections/claude-for-you"
        }

    def test_learn_accepts_only_academy_collections(self):
        from src.sitemap import filter_by_category

        entries = self._make_entries([
            "https://academy.claude.com/collections/build-with-claude",
            "https://academy.claude.com/collections",
            "https://academy.claude.com/courses/build-with-claude/lesson-1",
            "https://www.anthropic.com/learn/build-with-claude",
            "https://academy.claude.com.evil.test/collections/lookalike",
        ])

        assert filter_by_category(entries)["learn"] == {
            "https://academy.claude.com/collections/build-with-claude"
        }

    def test_excludes_non_matching_urls(self):
        from src.sitemap import filter_by_category

        entries = self._make_entries([
            "https://www.anthropic.com/",
            "https://www.anthropic.com/careers",
            "https://www.anthropic.com/about",
            "https://www.anthropic.com/news/article-1",
        ])

        result = filter_by_category(entries)

        assert result["news"] == {"https://www.anthropic.com/news/article-1"}
        assert result["research"] == set()
        assert result["engineering"] == set()
        assert result["learn"] == set()

    def test_multiple_urls_in_same_category(self):
        from src.sitemap import filter_by_category

        entries = self._make_entries([
            "https://www.anthropic.com/news/a",
            "https://www.anthropic.com/news/b",
            "https://www.anthropic.com/news/c",
        ])

        result = filter_by_category(entries)

        assert len(result["news"]) == 3

    def test_empty_entries(self):
        from src.sitemap import filter_by_category

        result = filter_by_category([])

        for category in ("news", "research", "engineering", "learn"):
            assert result[category] == set()

    def test_excludes_category_index_pages(self):
        """URLs like /news (without a slug) should be excluded."""
        from src.sitemap import filter_by_category

        entries = self._make_entries([
            "https://www.anthropic.com/news",
            "https://www.anthropic.com/news/real-article",
        ])

        result = filter_by_category(entries)

        assert result["news"] == {"https://www.anthropic.com/news/real-article"}
