"""Tests preventing empty or grossly partial sitemap initialization."""

import pytest


def test_snapshot_shape_rejects_empty_category_and_small_total():
    from src.sitemap import IncompleteSitemapError, validate_snapshot_shape

    with pytest.raises(IncompleteSitemapError):
        validate_snapshot_shape({
            "news": {"https://www.anthropic.com/news/a"},
            "research": set(),
            "engineering": set(),
            "learn": set(),
        })


def test_snapshot_shape_rejects_100_item_partial_snapshot():
    from src.sitemap import IncompleteSitemapError, validate_snapshot_shape

    with pytest.raises(IncompleteSitemapError):
        validate_snapshot_shape({
            "news": {f"https://www.anthropic.com/news/{index}" for index in range(97)},
            "research": {"https://www.anthropic.com/research/one"},
            "engineering": {"https://www.anthropic.com/engineering/one"},
            "learn": {"https://www.anthropic.com/learn/one"},
        })


def test_snapshot_shape_accepts_conservative_current_scale_floor():
    from src.sitemap import validate_snapshot_shape

    categorized = {
        "news": {f"https://www.anthropic.com/news/{index}" for index in range(200)},
        "research": {f"https://www.anthropic.com/research/{index}" for index in range(80)},
        "engineering": {f"https://www.anthropic.com/engineering/{index}" for index in range(19)},
        "learn": {"https://www.anthropic.com/learn/one"},
    }
    validate_snapshot_shape(categorized)
