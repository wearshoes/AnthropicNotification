"""Tests for durable category detection."""

from unittest.mock import patch


class TestDetectChanges:
    def test_new_urls_detected(self):
        from src.detector import detect_changes

        current = {"https://www.anthropic.com/news/a", "https://www.anthropic.com/news/b"}
        known = {"https://www.anthropic.com/news/a"}
        assert detect_changes(current, known) == {"https://www.anthropic.com/news/b"}

    def test_no_changes(self):
        from src.detector import detect_changes

        urls = {"https://www.anthropic.com/news/a"}
        assert detect_changes(urls, urls) == set()

    def test_first_run_is_silent(self):
        from src.detector import detect_changes

        current = {"https://www.anthropic.com/news/a"}
        assert detect_changes(current, set(), is_first_run=True) == set()

    def test_non_first_empty_baseline_detects_everything(self):
        from src.detector import detect_changes

        current = {"https://www.anthropic.com/news/a"}
        assert detect_changes(current, set()) == current


class TestProcessCategory:
    @patch("src.detector.issues")
    def test_first_run_creates_baseline_without_event(self, mock_issues):
        from src.detector import process_category

        current = {"https://www.anthropic.com/news/a"}
        mock_issues.get_baseline_issue.return_value = (None, set())
        assert process_category("news", current, [], []) == []
        mock_issues.create_baseline_issue.assert_called_once_with("news", current)

    @patch("src.detector.notifier.plan_events")
    @patch("src.detector.issues")
    def test_new_urls_create_outbox_before_union_baseline(self, mock_issues, mock_plan):
        from src.detector import process_category

        known = {"https://www.anthropic.com/news/a"}
        current = known | {"https://www.anthropic.com/news/b"}
        planned = object()
        persisted = object()
        mock_issues.get_baseline_issue.return_value = (1, known)
        mock_plan.return_value = [planned]
        mock_issues.create_outbox_issue.return_value = persisted

        assert process_category("news", current, [], [{"name": "target"}]) == [persisted]
        mock_plan.assert_called_once_with(
            "news", {"https://www.anthropic.com/news/b"}, [{"name": "target"}]
        )
        mock_issues.update_baseline_issue.assert_called_once_with(1, current)

    @patch("src.detector.issues")
    def test_no_changes_does_not_write_state(self, mock_issues):
        from src.detector import process_category

        urls = {"https://www.anthropic.com/news/a"}
        mock_issues.get_baseline_issue.return_value = (1, urls)
        assert process_category("news", urls, [], []) == []
        mock_issues.create_outbox_issue.assert_not_called()
        mock_issues.update_baseline_issue.assert_not_called()
