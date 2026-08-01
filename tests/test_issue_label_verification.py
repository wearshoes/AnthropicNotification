"""Adversarial tests for Issue labels and lifecycle write verification."""

from dataclasses import replace
import json
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


@patch("src.issues.subprocess.run")
def test_create_outbox_rejects_correct_body_without_recovery_labels(mock_run):
    from src.issues import GitHubStateError, _ensured_labels, create_outbox_issue
    from src.outbox import render_issue_body

    _ensured_labels.clear()
    event = _event()
    mock_run.side_effect = [
        MagicMock(returncode=0, stdout="", stderr=""),
        MagicMock(returncode=0, stdout="", stderr=""),
        MagicMock(returncode=0, stdout="", stderr=""),
        MagicMock(returncode=0, stdout="https://github.com/o/r/issues/101", stderr=""),
        MagicMock(returncode=0, stdout=json.dumps({
            "number": 101,
            "body": render_issue_body(event),
            "labels": [],
            "state": "CLOSED",
        }), stderr=""),
    ]

    with pytest.raises(GitHubStateError, match="open|label"):
        create_outbox_issue(event)


@patch("src.issues.subprocess.run")
def test_closed_pending_issue_fails_loudly_instead_of_disappearing(mock_run):
    from src.issues import GitHubStateError, list_pending_events
    from src.outbox import render_issue_body

    mock_run.return_value = MagicMock(returncode=0, stdout=json.dumps([[{
        "number": 101,
        "body": render_issue_body(_event()),
        "labels": [{"name": "update"}, {"name": "notification-pending"}],
        "state": "CLOSED",
    }]]), stderr="")

    with pytest.raises(GitHubStateError, match="closed"):
        list_pending_events()


@patch("src.issues.subprocess.run")
def test_open_outbox_with_removed_pending_label_is_repaired(mock_run):
    from src.issues import _ensured_labels, list_pending_events
    from src.outbox import render_issue_body

    _ensured_labels.clear()
    event = _event()
    unlabeled = {
        "number": 101,
        "body": render_issue_body(event),
        "labels": [{"name": "news"}, {"name": "update"}],
        "state": "OPEN",
    }
    repaired = {
        **unlabeled,
        "labels": [
            {"name": "news"},
            {"name": "update"},
            {"name": "notification-pending"},
        ],
    }
    mock_run.side_effect = [
        MagicMock(returncode=0, stdout=json.dumps([[unlabeled]]), stderr=""),
        MagicMock(returncode=0, stdout="", stderr=""),
        MagicMock(returncode=0, stdout="", stderr=""),
        MagicMock(returncode=0, stdout=json.dumps(repaired), stderr=""),
    ]

    events = list_pending_events()

    assert events[0].issue_number == 101
    assert ["gh", "issue", "edit", "101", "--add-label", "notification-pending"] in [
        entry.args[0] for entry in mock_run.call_args_list
    ]


@patch("src.issues.subprocess.run")
def test_finalize_re_reads_delivered_label_transition(mock_run):
    from src.issues import GitHubStateError, _ensured_labels, finalize_outbox_event
    from src.outbox import record_receipt

    _ensured_labels.clear()
    pending = replace(_event(), issue_number=101)
    delivered = record_receipt(pending, pending.chunks[0].chunk_id)
    mock_run.side_effect = [
        MagicMock(returncode=0, stdout="", stderr=""),
        MagicMock(returncode=0, stdout="", stderr=""),
        MagicMock(returncode=0, stdout=json.dumps({
            "number": 101,
            "body": "",
            "labels": [{"name": "notification-pending"}],
            "state": "OPEN",
        }), stderr=""),
    ]

    with pytest.raises(GitHubStateError, match="finalization"):
        finalize_outbox_event(delivered)
