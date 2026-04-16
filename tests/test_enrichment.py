"""Tests for src/enrichment.py — written BEFORE implementation."""

import pytest
from unittest.mock import patch, MagicMock


SAMPLE_HTML = """\
<!DOCTYPE html><html><head>
<title>Introducing Claude Opus 4.7 | Anthropic</title>
<meta property="og:title" content="Introducing Claude Opus 4.7"/>
<meta property="og:description" content="Our latest foundation model with improved reasoning."/>
<meta property="og:image" content="https://cdn.sanity.io/images/test/image-1920x1080.png"/>
</head><body></body></html>
"""

GENERIC_DESC_HTML = """\
<!DOCTYPE html><html><head>
<title>Some Page | Anthropic</title>
<meta property="og:title" content="Some Page"/>
<meta property="og:description" content="Anthropic is an AI safety and research company that's working to build reliable, interpretable, and steerable AI systems."/>
</head><body></body></html>
"""

MINIMAL_HTML = """\
<!DOCTYPE html><html><head>
<title>Bare Page</title>
</head><body></body></html>
"""


class TestEnrichUrl:
    """Tests for enrich_url()."""

    @patch("src.enrichment.requests.get")
    def test_extracts_og_metadata(self, mock_get):
        from src.enrichment import enrich_url

        mock_response = MagicMock()
        mock_response.text = SAMPLE_HTML
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = enrich_url("https://www.anthropic.com/news/claude-opus-4-7")

        assert result["url"] == "https://www.anthropic.com/news/claude-opus-4-7"
        assert result["title"] == "Introducing Claude Opus 4.7"
        assert "improved reasoning" in result["description"]
        assert "1920x1080" in result["image"]

    @patch("src.enrichment.requests.get")
    def test_falls_back_to_title_tag(self, mock_get):
        from src.enrichment import enrich_url

        mock_response = MagicMock()
        mock_response.text = MINIMAL_HTML
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = enrich_url("https://www.anthropic.com/news/bare-page")

        assert result["title"] == "Bare Page"
        assert result["description"] is None
        assert result["image"] is None

    @patch("src.enrichment.requests.get")
    def test_falls_back_to_slug_on_failure(self, mock_get):
        from src.enrichment import enrich_url
        import requests as req_lib

        mock_get.side_effect = req_lib.exceptions.ConnectionError("timeout")

        result = enrich_url("https://www.anthropic.com/news/some-article")

        assert result["title"] == "some-article"
        assert result["description"] is None
        assert result["image"] is None
        assert result["url"] == "https://www.anthropic.com/news/some-article"

    @patch("src.enrichment.requests.get")
    def test_filters_generic_description(self, mock_get):
        from src.enrichment import enrich_url

        mock_response = MagicMock()
        mock_response.text = GENERIC_DESC_HTML
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = enrich_url("https://www.anthropic.com/news/some-page")

        assert result["title"] == "Some Page"
        # Generic Anthropic description should be filtered out
        assert result["description"] is None


class TestEnrichUrls:
    """Tests for enrich_urls() — batch enrichment."""

    @patch("src.enrichment.enrich_url")
    def test_enriches_all_categories(self, mock_enrich):
        from src.enrichment import enrich_urls

        mock_enrich.return_value = {"url": "u", "title": "t", "description": "d", "image": "i"}

        changes = {
            "news": {"https://www.anthropic.com/news/a"},
            "research": {"https://www.anthropic.com/research/b"},
        }

        result = enrich_urls(changes)

        assert "news" in result
        assert "research" in result
        assert isinstance(result["news"], list)
        assert len(result["news"]) == 1
        assert mock_enrich.call_count == 2

    @patch("src.enrichment.enrich_url")
    def test_preserves_order_sorted_by_url(self, mock_enrich):
        from src.enrichment import enrich_urls

        def side_effect(url):
            return {"url": url, "title": url.split("/")[-1], "description": None, "image": None}

        mock_enrich.side_effect = side_effect

        changes = {"news": {"https://www.anthropic.com/news/b", "https://www.anthropic.com/news/a"}}

        result = enrich_urls(changes)

        assert result["news"][0]["url"] == "https://www.anthropic.com/news/a"
        assert result["news"][1]["url"] == "https://www.anthropic.com/news/b"
