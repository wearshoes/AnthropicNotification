"""Core tests for fail-closed GitHub Issue state."""

import json
import logging
from unittest.mock import MagicMock, patch

import pytest


def _baseline(number, body, category="news", state="OPEN"):
    return {
        "number": number,
        "body": body,
        "labels": [{"name": "baseline"}, {"name": category}],
        "state": state,
    }


class TestGetBaselineIssue:
    @patch("src.issues.subprocess.run")
    def test_returns_urls_when_baseline_exists(self, mock_run):
        from src.issues import get_baseline_issue

        mock_run.return_value = MagicMock(returncode=0, stdout=json.dumps([
            _baseline(
                1,
                "https://www.anthropic.com/news/a\n\n"
                "https://www.anthropic.com/news/b",
            )
        ]), stderr="")
        assert get_baseline_issue("news") == (
            1,
            {"https://www.anthropic.com/news/a", "https://www.anthropic.com/news/b"},
        )

    @patch("src.issues.subprocess.run")
    def test_returns_missing_only_for_empty_successful_query(self, mock_run):
        from src.issues import get_baseline_issue

        mock_run.return_value = MagicMock(returncode=0, stdout="[]", stderr="")
        assert get_baseline_issue("news") == (None, set())

    @patch("src.issues.subprocess.run")
    def test_rejects_wrong_category_or_closed_baseline_result(self, mock_run):
        from src.issues import GitHubStateError, get_baseline_issue

        mock_run.return_value = MagicMock(returncode=0, stdout=json.dumps([
            _baseline(1, "https://www.anthropic.com/news/a", "research", "CLOSED")
        ]), stderr="")

        with pytest.raises(GitHubStateError, match="Baseline query"):
            get_baseline_issue("news")


class TestCloseOldUpdateIssues:
    @patch("src.issues.subprocess.run")
    def test_closes_old_excludes_current_and_verifies_close(self, mock_run):
        from src.issues import close_old_update_issues

        mock_run.side_effect = [
            MagicMock(returncode=0, stdout=json.dumps([
                {"number": 5, "labels": []},
                {"number": 7, "labels": []},
            ]), stderr=""),
            MagicMock(returncode=0, stdout="", stderr=""),
            MagicMock(returncode=0, stdout=json.dumps({
                "number": 5, "body": "", "labels": [], "state": "CLOSED"
            }), stderr=""),
        ]
        close_old_update_issues("news", exclude_number=7)
        assert [entry.args[0] for entry in mock_run.call_args_list if "close" in entry.args[0]] == [
            ["gh", "issue", "close", "5"]
        ]

    @patch("src.issues.subprocess.run")
    def test_requires_excluded_current_issue(self, mock_run):
        from src.issues import close_old_update_issues

        with pytest.raises(ValueError, match="exclude_number"):
            close_old_update_issues("news")
        mock_run.assert_not_called()


class TestEnsureLabel:
    @patch("src.issues.subprocess.run")
    def test_successful_label_creation_is_cached(self, mock_run):
        from src.issues import _ensure_label, _ensured_labels

        _ensured_labels.clear()
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        _ensure_label("news")
        _ensure_label("news")
        assert mock_run.call_count == 1

    @patch("src.issues.subprocess.run")
    def test_failed_label_creation_is_not_cached(self, mock_run):
        from src.issues import GitHubCommandError, _ensure_label, _ensured_labels

        _ensured_labels.clear()
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="denied")
        with pytest.raises(GitHubCommandError):
            _ensure_label("news")
        assert "news" not in _ensured_labels


class TestRunGh:
    @patch("src.issues.subprocess.run")
    def test_failure_logs_and_raises(self, mock_run, caplog):
        from src.issues import GitHubCommandError, _run_gh

        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="could not add label")
        with caplog.at_level(logging.ERROR, logger="src.issues"):
            with pytest.raises(GitHubCommandError, match="could not add label"):
                _run_gh(["issue", "create"])
        assert "gh command failed" in caplog.text

    @patch("src.issues.subprocess.run")
    def test_success_has_no_error_log(self, mock_run, caplog):
        from src.issues import _run_gh

        mock_run.return_value = MagicMock(returncode=0, stdout="[]", stderr="")
        with caplog.at_level(logging.ERROR, logger="src.issues"):
            _run_gh(["issue", "list"])
        assert "gh command failed" not in caplog.text
