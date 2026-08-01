"""Tests for split-event durability and conflicting pending ownership."""

from dataclasses import replace
from unittest.mock import patch

import pytest


def _event(url, category="news", issue_number=None):
    from src.outbox import build_event, make_destination_id, make_item

    item = make_item(category, url)
    event = build_event(
        category,
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
    return replace(event, issue_number=issue_number)


@patch("src.detector.notifier.plan_events")
@patch("src.detector.issues")
def test_all_split_events_are_persisted_before_baseline(mock_issues, mock_plan):
    from src.detector import process_category

    first = _event("https://www.anthropic.com/news/a")
    second = _event("https://www.anthropic.com/news/b")
    calls = []
    mock_issues.get_baseline_issue.return_value = (45, set())
    mock_plan.return_value = [first, second]
    persisted = [
        replace(first, issue_number=101),
        replace(second, issue_number=102),
    ]
    mock_issues.create_outbox_issue.side_effect = [
        calls.append("outbox-1") or persisted[0],
        calls.append("outbox-2") or persisted[1],
    ]
    mock_issues.update_baseline_issue.side_effect = lambda *args: calls.append("baseline")

    result = process_category(
        "news",
        {item.url for event in (first, second) for item in event.items},
        [],
        [{"name": "wechat_work"}],
    )

    assert result == persisted
    assert calls == ["outbox-1", "outbox-2", "baseline"]


@patch("src.main.sitemap")
@patch("src.main.detector")
@patch("src.main.issues")
@patch("src.main.notifier")
def test_duplicate_owner_is_quarantined_without_blocking_unrelated_pending(
    mock_notifier, mock_issues, mock_detector, mock_sitemap
):
    from src.main import PipelineDeliveryError, run

    first_owner = _event("https://www.anthropic.com/news/a", issue_number=101)
    second_owner = replace(first_owner, issue_number=102)
    unrelated = _event(
        "https://www.anthropic.com/research/a",
        category="research",
        issue_number=103,
    )
    mock_issues.list_pending_events.return_value = [
        first_owner, second_owner, unrelated
    ]
    mock_notifier.discover_formatters.return_value = [{"name": "wechat_work"}]
    mock_notifier.deliver_event.return_value = unrelated
    mock_sitemap.fetch_sitemap.return_value = []
    mock_sitemap.filter_by_category.return_value = {
        "news": set(), "research": set(), "engineering": set(), "learn": set()
    }
    mock_detector.process_category.return_value = []

    with pytest.raises(PipelineDeliveryError, match="multiple owners"):
        run()

    mock_notifier.deliver_event.assert_called_once()
    assert mock_notifier.deliver_event.call_args.args[0] == unrelated
