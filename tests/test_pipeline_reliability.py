"""Failure-oriented tests for durable detection and delivery orchestration."""

from dataclasses import replace
from unittest.mock import MagicMock, patch

import pytest


def _formatter(name="wechat_work", max_items=8):
    module = MagicMock()
    module.FORMATTER_VERSION = 1
    module.MAX_ITEMS_PER_MESSAGE = max_items
    module.format_message.side_effect = lambda changes: {
        "items": [item["url"] for values in changes.values() for item in values]
    }
    return {
        "name": name,
        "module": module,
        "webhook_url": f"https://hooks.example/{name}",
    }


def _event(target="wechat_work"):
    from src.outbox import build_event, make_destination_id, make_item

    item = make_item("news", "https://www.anthropic.com/news/a")
    return build_event(
        "news",
        (item,),
        [{
            "target": target,
            "destination_id": make_destination_id(f"https://hooks.example/{target}"),
            "formatter_version": 1,
            "item_ids": [item.item_id],
            "payload": {"urls": [item.url]},
        }],
        created_at="2026-08-02T00:00:00Z",
    )


@patch("src.notifier.enrich_urls")
def test_plan_event_splits_sixteen_wechat_items_without_loss(mock_enrich):
    from src.notifier import plan_event

    urls = {f"https://www.anthropic.com/news/{index:02d}" for index in range(16)}
    mock_enrich.return_value = {"news": [{
        "url": url, "title": url.rsplit("/", 1)[-1],
        "description": None, "image": None,
    } for url in sorted(urls)]}
    event = plan_event("news", urls, [_formatter()], created_at="2026-08-02T00:00:00Z")
    assert [len(chunk.item_ids) for chunk in event.chunks] == [8, 8]
    assert set().union(*(set(chunk.item_ids) for chunk in event.chunks)) == {
        item.item_id for item in event.items
    }


def test_plan_event_without_targets_is_blocked():
    from src.notifier import NoNotificationTargetsError, plan_event

    with pytest.raises(NoNotificationTargetsError):
        plan_event("news", {"https://www.anthropic.com/news/a"}, [])


def test_delivery_saves_success_and_surfaces_independent_failure():
    from src.notifier import DeliveryError, deliver_event
    from src.outbox import build_event, make_destination_id, make_item

    item = make_item("news", "https://www.anthropic.com/news/a")
    event = replace(build_event(
        "news", (item,), [
            {"target": "failing", "destination_id": make_destination_id("https://hooks.example/failing"), "formatter_version": 1,
             "item_ids": [item.item_id], "payload": {"target": "failing"}},
            {"target": "passing", "destination_id": make_destination_id("https://hooks.example/passing"), "formatter_version": 1,
             "item_ids": [item.item_id], "payload": {"target": "passing"}},
        ], created_at="2026-08-02T00:00:00Z",
    ), issue_number=101)
    failing, passing = _formatter("failing", 1), _formatter("passing", 1)
    failing["module"].send.side_effect = RuntimeError("rejected")
    save = MagicMock(side_effect=lambda value: value)
    with pytest.raises(DeliveryError) as raised:
        deliver_event(event, [failing, passing], save_event=save)
    assert save.call_count == 1
    assert raised.value.event.receipts == frozenset({event.chunks[1].chunk_id})


@patch("src.detector.notifier.plan_events")
@patch("src.detector.issues")
def test_detector_persists_before_monotonic_baseline(mock_issues, mock_plan):
    from src.detector import process_category

    known = {"https://www.anthropic.com/news/a", "https://www.anthropic.com/news/retired"}
    current = {"https://www.anthropic.com/news/a", "https://www.anthropic.com/news/b"}
    event = replace(_event(), issue_number=101)
    calls = []
    mock_issues.get_baseline_issue.return_value = (45, known)
    mock_plan.return_value = [replace(event, issue_number=None)]
    mock_issues.create_outbox_issue.side_effect = lambda value: calls.append("outbox") or event
    mock_issues.update_baseline_issue.side_effect = lambda *args: calls.append("baseline")
    assert process_category("news", current, [], [_formatter()]) == [event]
    assert calls == ["outbox", "baseline"]


@patch("src.detector.notifier.plan_events")
@patch("src.detector.issues")
def test_detector_subtracts_pending_items(mock_issues, mock_plan):
    from src.detector import process_category

    pending = replace(_event(), issue_number=101)
    current = {"https://www.anthropic.com/news/a"}
    mock_issues.get_baseline_issue.return_value = (45, set())
    assert process_category("news", current, [pending], [_formatter()]) == []
    mock_plan.assert_not_called()
    mock_issues.update_baseline_issue.assert_called_once_with(45, current)


@patch("src.main.sitemap")
@patch("src.main.issues")
@patch("src.main.notifier")
@patch("src.main.detector")
def test_pending_delivery_precedes_sitemap_failure(
    mock_detector, mock_notifier, mock_issues, mock_sitemap
):
    from src.main import run

    event = replace(_event(), issue_number=101)
    mock_issues.list_pending_events.return_value = [event]
    mock_notifier.discover_formatters.return_value = [_formatter()]
    mock_notifier.deliver_event.return_value = event
    mock_sitemap.fetch_sitemaps.side_effect = RuntimeError("sitemap unavailable")
    with pytest.raises(RuntimeError, match="sitemap unavailable"):
        run()
    mock_detector.ensure_event_in_baseline.assert_called_once_with(event)
    mock_notifier.deliver_event.assert_called_once()
