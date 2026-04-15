"""Tests for src/main.py — written BEFORE implementation."""

import pytest
from unittest.mock import patch, MagicMock, call


class TestRun:
    """Tests for run() — main orchestrator."""

    @patch("src.main.notifier")
    @patch("src.main.detector")
    @patch("src.main.sitemap")
    def test_full_flow_with_new_urls(self, mock_sitemap, mock_detector, mock_notifier):
        from src.main import run

        # Sitemap returns entries
        mock_sitemap.fetch_sitemap.return_value = [
            {"loc": "https://www.anthropic.com/news/a", "lastmod": None},
            {"loc": "https://www.anthropic.com/research/b", "lastmod": None},
        ]
        mock_sitemap.filter_by_category.return_value = {
            "news": {"https://www.anthropic.com/news/a"},
            "research": {"https://www.anthropic.com/research/b"},
            "engineering": set(),
            "learn": set(),
        }

        # Detector finds new URLs (only called for non-empty categories)
        mock_detector.process_category.side_effect = [
            {"https://www.anthropic.com/news/a"},  # news
            {"https://www.anthropic.com/research/b"},  # research
        ]

        # Notifier
        mock_notifier.discover_formatters.return_value = [{"name": "test"}]

        run()

        mock_sitemap.fetch_sitemap.assert_called_once()
        assert mock_detector.process_category.call_count == 2  # only non-empty categories
        mock_notifier.send_notifications.assert_called_once()
        # Check changes dict passed to notifier
        changes_arg = mock_notifier.send_notifications.call_args[0][1]
        assert "news" in changes_arg
        assert "research" in changes_arg

    @patch("src.main.notifier")
    @patch("src.main.detector")
    @patch("src.main.sitemap")
    def test_no_changes_skips_notification(self, mock_sitemap, mock_detector, mock_notifier):
        from src.main import run

        mock_sitemap.fetch_sitemap.return_value = []
        mock_sitemap.filter_by_category.return_value = {
            "news": set(), "research": set(), "engineering": set(), "learn": set(),
        }
        mock_detector.process_category.return_value = set()
        mock_notifier.discover_formatters.return_value = []

        run()

        mock_notifier.send_notifications.assert_not_called()

    @patch("src.main.notifier")
    @patch("src.main.detector")
    @patch("src.main.sitemap")
    def test_sitemap_error_raises(self, mock_sitemap, mock_detector, mock_notifier):
        from src.main import run

        mock_sitemap.fetch_sitemap.side_effect = Exception("network error")

        with pytest.raises(Exception, match="network error"):
            run()


class TestDryRun:
    """Tests for run(dry_run=True)."""

    @patch("src.main.notifier")
    @patch("src.main.detector")
    @patch("src.main.sitemap")
    def test_dry_run_skips_detection_and_notification(self, mock_sitemap, mock_detector, mock_notifier):
        from src.main import run

        mock_sitemap.fetch_sitemap.return_value = [
            {"loc": "https://www.anthropic.com/news/a", "lastmod": "2026-04-16"},
        ]
        mock_sitemap.filter_by_category.return_value = {
            "news": {"https://www.anthropic.com/news/a"},
            "research": set(),
            "engineering": set(),
            "learn": set(),
        }

        result = run(dry_run=True)

        mock_sitemap.fetch_sitemap.assert_called_once()
        mock_sitemap.filter_by_category.assert_called_once()
        mock_detector.process_category.assert_not_called()
        mock_notifier.send_notifications.assert_not_called()
        # Should return the categorized URLs
        assert "news" in result
