"""Failure-oriented tests for GitHub Issue state and outbox persistence."""

from dataclasses import replace
import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest


def _event():
    from src.outbox import build_event, make_destination_id, make_item

    item = make_item("news", "https://www.anthropic.com/news/a")
    return build_event(
        "news",
        (item,),
        [{
            "target": "wechat_work",
            "destination_id": make_destination_id("https://hooks.example/wechat_work"),
            "formatter_version": 1,
            "item_ids": [item.item_id],
            "payload": {"msgtype": "news"},
        }],
        created_at="2026-08-02T00:00:00Z",
    )


def _outbox_json(event, number=101, *, delivered=False):
    from src.outbox import render_issue_body

    labels = [
        {"name": event.category},
        {"name": "update"},
        {"name": "notification-delivered" if delivered else "notification-pending"},
    ]
    return json.dumps({
        "number": number,
        "body": render_issue_body(event),
        "labels": labels,
        "state": "OPEN",
    })


@patch("src.issues.subprocess.run")
def test_run_gh_nonzero_raises_state_error(mock_run):
    from src.issues import GitHubCommandError, _run_gh

    mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="401 Bad credentials")
    with pytest.raises(GitHubCommandError, match="401 Bad credentials"):
        _run_gh(["issue", "list"])


@patch("src.issues.subprocess.run")
def test_run_gh_has_timeout(mock_run):
    from src.issues import _run_gh

    mock_run.return_value = MagicMock(returncode=0, stdout="[]", stderr="")
    _run_gh(["issue", "list"])
    assert mock_run.call_args.kwargs["timeout"] == 30


@patch("src.issues.subprocess.run")
def test_run_gh_timeout_raises_state_error(mock_run):
    from src.issues import GitHubCommandError, _run_gh

    mock_run.side_effect = subprocess.TimeoutExpired(["gh", "issue", "list"], 30)
    with pytest.raises(GitHubCommandError, match="timed out"):
        _run_gh(["issue", "list"])


@patch("src.issues.subprocess.run")
def test_baseline_query_failure_is_not_missing(mock_run):
    from src.issues import GitHubCommandError, get_baseline_issue

    mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="504 Gateway Timeout")
    with pytest.raises(GitHubCommandError):
        get_baseline_issue("news")


@patch("src.issues.subprocess.run")
def test_baseline_invalid_json_fails_closed(mock_run):
    from src.issues import GitHubStateError, get_baseline_issue

    mock_run.return_value = MagicMock(returncode=0, stdout="not-json", stderr="")
    with pytest.raises(GitHubStateError, match="Invalid JSON"):
        get_baseline_issue("news")


@patch("src.issues.subprocess.run")
def test_baseline_duplicates_select_highest(mock_run):
    from src.issues import get_baseline_issue

    mock_run.return_value = MagicMock(returncode=0, stdout=json.dumps([
        {"number": 3, "body": "https://www.anthropic.com/news/old",
         "labels": [{"name": "baseline"}, {"name": "news"}], "state": "OPEN"},
        {"number": 45, "body": "https://www.anthropic.com/news/current",
         "labels": [{"name": "baseline"}, {"name": "news"}], "state": "OPEN"},
    ]), stderr="")
    assert get_baseline_issue("news") == (
        45, {"https://www.anthropic.com/news/current"}
    )


@patch("src.issues.subprocess.run")
def test_create_outbox_re_reads_body_labels_and_state(mock_run):
    from src.issues import _ensured_labels, create_outbox_issue

    _ensured_labels.clear()
    event = _event()
    mock_run.side_effect = [
        MagicMock(returncode=0, stdout="", stderr=""),
        MagicMock(returncode=0, stdout="", stderr=""),
        MagicMock(returncode=0, stdout="", stderr=""),
        MagicMock(returncode=0, stdout="https://github.com/o/r/issues/101", stderr=""),
        MagicMock(returncode=0, stdout=_outbox_json(event), stderr=""),
    ]
    assert create_outbox_issue(event).issue_number == 101


@patch("src.issues.subprocess.run")
def test_create_outbox_rejects_missing_issue_number(mock_run):
    from src.issues import GitHubStateError, _ensured_labels, create_outbox_issue

    _ensured_labels.clear()
    mock_run.return_value = MagicMock(returncode=0, stdout="unexpected", stderr="")
    with pytest.raises(GitHubStateError, match="issue number"):
        create_outbox_issue(_event())


@patch("src.issues.subprocess.run")
def test_list_pending_events_parses_machine_state(mock_run):
    from src.issues import list_pending_events

    event = _event()
    data = json.loads(_outbox_json(event))
    mock_run.return_value = MagicMock(returncode=0, stdout=json.dumps([[data]]), stderr="")
    assert list_pending_events()[0].issue_number == 101


@patch("src.issues.subprocess.run")
def test_list_pending_events_recovers_outbox_from_later_api_page(mock_run):
    from src.issues import list_pending_events

    event = _event()
    data = json.loads(_outbox_json(event))
    data["state"] = "open"
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout=json.dumps([[], [data]]),
        stderr="",
    )

    assert list_pending_events()[0].issue_number == 101
    command = mock_run.call_args.args[0]
    assert command[:4] == ["gh", "api", "--method", "GET"]
    assert "--paginate" in command
    assert "--slurp" in command
    assert "--limit" not in command


@patch("src.issues.subprocess.run")
def test_list_pending_events_rejects_malformed_pull_request_marker(mock_run):
    from src.issues import GitHubStateError, list_pending_events

    event = _event()
    data = json.loads(_outbox_json(event))
    data["state"] = "open"
    data["pull_request"] = None
    mock_run.return_value = MagicMock(
        returncode=0, stdout=json.dumps([[data]]), stderr=""
    )

    with pytest.raises(GitHubStateError, match="pull_request"):
        list_pending_events()


@patch("src.issues.subprocess.run")
def test_list_pending_events_skips_well_formed_pull_request(mock_run):
    from src.issues import list_pending_events

    event = _event()
    data = json.loads(_outbox_json(event))
    data["pull_request"] = {
        "url": "https://api.github.com/repos/o/r/pulls/101"
    }
    mock_run.return_value = MagicMock(
        returncode=0, stdout=json.dumps([[data]]), stderr=""
    )

    assert list_pending_events() == []

@patch("src.issues.subprocess.run")
def test_save_outbox_event_verifies_receipt(mock_run):
    from src.issues import save_outbox_event
    from src.outbox import record_receipt

    persisted = replace(_event(), issue_number=101)
    delivered = record_receipt(persisted, persisted.chunks[0].chunk_id)
    mock_run.side_effect = [
        MagicMock(returncode=0, stdout="", stderr=""),
        MagicMock(returncode=0, stdout=_outbox_json(delivered), stderr=""),
    ]
    assert save_outbox_event(delivered) == delivered


@patch("src.issues.subprocess.run")
def test_finalize_requires_receipts_and_verifies_labels(mock_run):
    from src.issues import _ensured_labels, finalize_outbox_event
    from src.outbox import record_receipt

    _ensured_labels.clear()
    persisted = replace(_event(), issue_number=101)
    with pytest.raises(ValueError, match="not fully delivered"):
        finalize_outbox_event(persisted)
    delivered = record_receipt(persisted, persisted.chunks[0].chunk_id)
    mock_run.side_effect = [
        MagicMock(returncode=0, stdout="", stderr=""),
        MagicMock(returncode=0, stdout="", stderr=""),
        MagicMock(returncode=0, stdout=_outbox_json(delivered, delivered=True), stderr=""),
    ]
    finalize_outbox_event(delivered)
