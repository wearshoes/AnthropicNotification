"""Tests for verified baseline writes and pending-safe cleanup."""

import json
from unittest.mock import MagicMock, patch

import pytest


def _baseline(number, body, category="news"):
    return json.dumps({
        "number": number,
        "body": body,
        "labels": [{"name": "baseline"}, {"name": category}],
        "state": "OPEN",
    })


@patch("src.issues.subprocess.run")
def test_create_baseline_re_reads_created_issue(mock_run):
    from src.issues import _ensured_labels, create_baseline_issue

    _ensured_labels.clear()
    url = "https://www.anthropic.com/news/a"
    mock_run.side_effect = [
        MagicMock(returncode=0, stdout="", stderr=""),
        MagicMock(returncode=0, stdout="", stderr=""),
        MagicMock(returncode=0, stdout="https://github.com/o/r/issues/45", stderr=""),
        MagicMock(returncode=0, stdout=_baseline(45, url), stderr=""),
    ]
    assert create_baseline_issue("news", {url}) == 45


@patch("src.issues.subprocess.run")
def test_update_baseline_rejects_non_monotonic_write(mock_run):
    from src.issues import GitHubStateError, update_baseline_issue

    old = "https://www.anthropic.com/news/a\nhttps://www.anthropic.com/news/b"
    mock_run.return_value = MagicMock(returncode=0, stdout=_baseline(45, old), stderr="")
    with pytest.raises(GitHubStateError, match="remove known URLs"):
        update_baseline_issue(45, {"https://www.anthropic.com/news/a"})
    assert mock_run.call_count == 1


@patch("src.issues.subprocess.run")
def test_update_baseline_verifies_exact_saved_union(mock_run):
    from src.issues import update_baseline_issue

    old = "https://www.anthropic.com/news/a"
    new = "https://www.anthropic.com/news/b"
    mock_run.side_effect = [
        MagicMock(returncode=0, stdout=_baseline(45, old), stderr=""),
        MagicMock(returncode=0, stdout="", stderr=""),
        MagicMock(returncode=0, stdout=_baseline(45, f"{old}\n{new}"), stderr=""),
    ]
    update_baseline_issue(45, {old, new})
    assert mock_run.call_count == 3


@patch("src.issues.subprocess.run")
def test_close_old_updates_never_closes_pending_events(mock_run):
    from src.issues import close_old_update_issues

    mock_run.side_effect = [
        MagicMock(returncode=0, stdout=json.dumps([
            {"number": 40, "labels": [{"name": "notification-delivered"}]},
            {"number": 41, "labels": [{"name": "notification-pending"}]},
            {"number": 45, "labels": [{"name": "notification-delivered"}]},
        ]), stderr=""),
        MagicMock(returncode=0, stdout="", stderr=""),
        MagicMock(returncode=0, stdout=json.dumps({
            "number": 40, "body": "", "labels": [], "state": "CLOSED"
        }), stderr=""),
    ]
    close_old_update_issues("news", exclude_number=45)
    close_commands = [entry.args[0] for entry in mock_run.call_args_list if "close" in entry.args[0]]
    assert close_commands == [["gh", "issue", "close", "40"]]
