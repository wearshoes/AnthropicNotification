"""Tests for src/detector.py — written BEFORE implementation."""

import pytest
from unittest.mock import patch, MagicMock


class TestDetectChanges:
    """Tests for detect_changes()."""

    def test_new_urls_detected(self):
        from src.detector import detect_changes

        current = {"https://www.anthropic.com/news/a", "https://www.anthropic.com/news/b", "https://www.anthropic.com/news/c"}
        known = {"https://www.anthropic.com/news/a", "https://www.anthropic.com/news/b"}

        new_urls = detect_changes(current, known)

        assert new_urls == {"https://www.anthropic.com/news/c"}

    def test_no_changes(self):
        from src.detector import detect_changes

        urls = {"https://www.anthropic.com/news/a", "https://www.anthropic.com/news/b"}

        new_urls = detect_changes(urls, urls)

        assert new_urls == set()

    def test_empty_known_returns_empty(self):
        """First run with no baseline: should return empty (silent baseline creation)."""
        from src.detector import detect_changes

        current = {"https://www.anthropic.com/news/a"}

        new_urls = detect_changes(current, known=set(), is_first_run=True)

        assert new_urls == set()

    def test_non_first_run_with_empty_known_returns_all(self):
        """If known is empty but it's not first run, treat as new."""
        from src.detector import detect_changes

        current = {"https://www.anthropic.com/news/a", "https://www.anthropic.com/news/b"}

        new_urls = detect_changes(current, known=set(), is_first_run=False)

        assert new_urls == current


class TestProcessCategory:
    """Tests for process_category() — orchestrates detection + issue management."""

    @patch("src.detector.issues")
    def test_first_run_creates_baseline_no_notification(self, mock_issues):
        from src.detector import process_category

        mock_issues.get_baseline_issue.return_value = (None, set())

        current_urls = {"https://www.anthropic.com/news/a", "https://www.anthropic.com/news/b"}

        new_urls = process_category("news", current_urls)

        assert new_urls == set()
        mock_issues.create_baseline_issue.assert_called_once_with("news", current_urls)
        mock_issues.create_update_issue.assert_not_called()

    @patch("src.detector.issues")
    def test_new_urls_create_aggregated_issue_and_close_old(self, mock_issues):
        from src.detector import process_category

        known = {"https://www.anthropic.com/news/a"}
        mock_issues.get_baseline_issue.return_value = (1, known)
        mock_issues.create_update_issue.return_value = 7

        current_urls = {"https://www.anthropic.com/news/a", "https://www.anthropic.com/news/b"}

        new_urls = process_category("news", current_urls)

        assert new_urls == {"https://www.anthropic.com/news/b"}
        # Called once with the full set of new URLs (not once per URL)
        mock_issues.create_update_issue.assert_called_once_with("news", {"https://www.anthropic.com/news/b"})
        mock_issues.close_old_update_issues.assert_called_once_with("news", exclude_number=7)
        mock_issues.update_baseline_issue.assert_called_once_with(1, current_urls)

    @patch("src.detector.issues")
    def test_no_changes_does_nothing(self, mock_issues):
        from src.detector import process_category

        urls = {"https://www.anthropic.com/news/a"}
        mock_issues.get_baseline_issue.return_value = (1, urls)

        new_urls = process_category("news", urls)

        assert new_urls == set()
        mock_issues.create_update_issue.assert_not_called()
        mock_issues.close_old_update_issues.assert_not_called()
        mock_issues.update_baseline_issue.assert_not_called()
