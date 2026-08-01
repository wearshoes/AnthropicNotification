"""Tests for trusted Anthropic inputs."""

from unittest.mock import MagicMock, patch


def test_sitemap_filter_rejects_lookalike_and_non_https_origins():
    from src.sitemap import filter_by_category

    entries = [
        {"loc": "https://www.anthropic.com/news/valid", "lastmod": None},
        {"loc": "https://www.anthropic.com.evil.test/news/invalid", "lastmod": None},
        {"loc": "http://www.anthropic.com/news/insecure", "lastmod": None},
        {"loc": "https://user@www.anthropic.com/news/credentials", "lastmod": None},
    ]
    assert filter_by_category(entries)["news"] == {
        "https://www.anthropic.com/news/valid"
    }


@patch("src.enrichment.requests.get")
def test_enrichment_rejects_cross_origin_redirect_before_following(mock_get):
    from src.enrichment import enrich_url

    redirect = MagicMock(
        status_code=302,
        headers={"Location": "http://169.254.169.254/latest"},
    )
    mock_get.return_value = redirect
    result = enrich_url("https://www.anthropic.com/news/a")
    assert result["title"] == "a"
    assert mock_get.call_count == 1
    assert mock_get.call_args.kwargs["allow_redirects"] is False
