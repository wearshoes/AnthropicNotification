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
        from src.issues import create_baseline_issue

        mock_run.return_value = MagicMock(returncode=0, stdout="")

        urls = {"https://www.anthropic.com/news/a", "https://www.anthropic.com/news/b"}
        create_baseline_issue("news", urls)

        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "gh" in cmd
        assert "issue" in cmd
        assert "create" in cmd
        # Check labels
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
        from src.issues import create_update_issue

        mock_run.return_value = MagicMock(returncode=0, stdout="")

        create_update_issue("news", "https://www.anthropic.com/news/new-article")

        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "issue" in cmd
        assert "create" in cmd
        label_idx = cmd.index("--label")
        assert "news,update" in cmd[label_idx + 1]

    @patch("src.issues.subprocess.run")
    def test_title_derived_from_url_slug(self, mock_run):
        from src.issues import create_update_issue

        mock_run.return_value = MagicMock(returncode=0, stdout="")

        create_update_issue("news", "https://www.anthropic.com/news/project-glasswing")

        cmd = mock_run.call_args[0][0]
        title_idx = cmd.index("--title")
        title = cmd[title_idx + 1]
        assert "project-glasswing" in title.lower() or "Project Glasswing" in title
