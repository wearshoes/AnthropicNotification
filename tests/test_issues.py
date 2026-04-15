"""Tests for src/issues.py — written BEFORE implementation."""

import json
import pytest
from unittest.mock import patch, MagicMock, call


class TestGetBaselineIssue:
    """Tests for get_baseline_issue()."""

    @patch("src.issues.subprocess.run")
    def test_returns_urls_when_baseline_exists(self, mock_run):
        from src.issues import get_baseline_issue

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps([{
                "number": 1,
                "body": "https://www.anthropic.com/news/a\nhttps://www.anthropic.com/news/b\n",
            }]),
        )

        number, urls = get_baseline_issue("news")

        assert number == 1
        assert urls == {"https://www.anthropic.com/news/a", "https://www.anthropic.com/news/b"}

    @patch("src.issues.subprocess.run")
    def test_returns_empty_when_no_baseline(self, mock_run):
        from src.issues import get_baseline_issue

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps([]),
        )

        number, urls = get_baseline_issue("news")

        assert number is None
        assert urls == set()

    @patch("src.issues.subprocess.run")
    def test_ignores_blank_lines_in_body(self, mock_run):
        from src.issues import get_baseline_issue

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps([{
                "number": 5,
                "body": "https://www.anthropic.com/news/a\n\n\nhttps://www.anthropic.com/news/b\n",
            }]),
        )

        number, urls = get_baseline_issue("news")

        assert number == 5
        assert len(urls) == 2


class TestCreateBaselineIssue:
    """Tests for create_baseline_issue()."""

    @patch("src.issues.subprocess.run")
    def test_creates_issue_with_correct_labels(self, mock_run):
        from src.issues import create_baseline_issue, _ensured_labels
        _ensured_labels.clear()

        mock_run.return_value = MagicMock(returncode=0, stdout="")

        urls = {"https://www.anthropic.com/news/a", "https://www.anthropic.com/news/b"}
        create_baseline_issue("news", urls)

        # Find the issue create call (skip label create calls)
        create_calls = [c for c in mock_run.call_args_list if "issue" in c[0][0] and "create" in c[0][0]]
        assert len(create_calls) == 1
        cmd = create_calls[0][0][0]
        label_idx = cmd.index("--label")
        assert "baseline,news" in cmd[label_idx + 1]


class TestUpdateBaselineIssue:
    """Tests for update_baseline_issue()."""

    @patch("src.issues.subprocess.run")
    def test_edits_issue_body(self, mock_run):
        from src.issues import update_baseline_issue

        mock_run.return_value = MagicMock(returncode=0, stdout="")

        urls = {"https://www.anthropic.com/news/a", "https://www.anthropic.com/news/b"}
        update_baseline_issue(1, urls)

        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "gh" in cmd
        assert "issue" in cmd
        assert "edit" in cmd
        assert "1" in [str(c) for c in cmd]


class TestCreateUpdateIssue:
    """Tests for create_update_issue()."""

    @patch("src.issues.subprocess.run")
    def test_creates_issue_for_new_url(self, mock_run):
        from src.issues import create_update_issue, _ensured_labels
        _ensured_labels.clear()

        mock_run.return_value = MagicMock(returncode=0, stdout="")

        create_update_issue("news", "https://www.anthropic.com/news/new-article")

        # Find the issue create call (skip label create calls)
        create_calls = [c for c in mock_run.call_args_list if "issue" in c[0][0] and "create" in c[0][0]]
        assert len(create_calls) == 1
        cmd = create_calls[0][0][0]
        label_idx = cmd.index("--label")
        assert "news,update" in cmd[label_idx + 1]

    @patch("src.issues.subprocess.run")
    def test_title_derived_from_url_slug(self, mock_run):
        from src.issues import create_update_issue, _ensured_labels
        _ensured_labels.clear()

        mock_run.return_value = MagicMock(returncode=0, stdout="")

        create_update_issue("news", "https://www.anthropic.com/news/project-glasswing")

        # Find the issue create call
        create_calls = [c for c in mock_run.call_args_list if "issue" in c[0][0] and "create" in c[0][0]]
        cmd = create_calls[0][0][0]
        title_idx = cmd.index("--title")
        title = cmd[title_idx + 1]
        assert "project-glasswing" in title.lower() or "Project Glasswing" in title


class TestEnsureLabel:
    """Tests for _ensure_label() — idempotent label creation with caching."""

    @patch("src.issues.subprocess.run")
    def test_creates_label_with_force_flag(self, mock_run):
        from src.issues import _ensure_label, _ensured_labels
        _ensured_labels.clear()

        mock_run.return_value = MagicMock(returncode=0, stdout="")

        _ensure_label("baseline")

        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "label" in cmd
        assert "create" in cmd
        assert "baseline" in cmd
        assert "--force" in cmd

    @patch("src.issues.subprocess.run")
    def test_caches_label_avoids_duplicate_call(self, mock_run):
        from src.issues import _ensure_label, _ensured_labels
        _ensured_labels.clear()

        mock_run.return_value = MagicMock(returncode=0, stdout="")

        _ensure_label("news")
        _ensure_label("news")  # second call should be cached

        # Only one subprocess call, not two
        assert mock_run.call_count == 1

    @patch("src.issues.subprocess.run")
    def test_different_labels_each_get_created(self, mock_run):
        from src.issues import _ensure_label, _ensured_labels
        _ensured_labels.clear()

        mock_run.return_value = MagicMock(returncode=0, stdout="")

        _ensure_label("baseline")
        _ensure_label("news")

        assert mock_run.call_count == 2


class TestRunGhErrorLogging:
    """Tests for _run_gh() error logging."""

    @patch("src.issues.subprocess.run")
    def test_logs_error_on_failure(self, mock_run, caplog):
        import logging
        from src.issues import _run_gh

        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="some output",
            stderr="could not add label: 'baseline' not found",
        )

        with caplog.at_level(logging.ERROR, logger="src.issues"):
            _run_gh(["issue", "create", "--title", "test"])

        assert "gh command failed" in caplog.text
        assert "could not add label" in caplog.text

    @patch("src.issues.subprocess.run")
    def test_no_log_on_success(self, mock_run, caplog):
        import logging
        from src.issues import _run_gh

        mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")

        with caplog.at_level(logging.ERROR, logger="src.issues"):
            _run_gh(["issue", "list"])

        assert "gh command failed" not in caplog.text
