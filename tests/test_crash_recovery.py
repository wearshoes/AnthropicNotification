"""Crash-window tests for outbox-before-baseline recovery."""

from dataclasses import replace
from unittest.mock import MagicMock, patch

import pytest


def _pending_event():
    from src.outbox import build_event, make_destination_id, make_item

    item = make_item("news", "https://www.anthropic.com/news/new")
    return replace(build_event(
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
    ), issue_number=101)


@patch("src.detector.issues")
def test_pending_event_repairs_baseline_from_its_own_items(mock_issues):
    from src.detector import ensure_event_in_baseline

    event = _pending_event()
    old = "https://www.anthropic.com/news/old"
    mock_issues.get_baseline_issue.return_value = (45, {old})

    ensure_event_in_baseline(event)

    mock_issues.update_baseline_issue.assert_called_once_with(
        45, {old, event.items[0].url}
    )


def test_second_delivery_run_skips_receipted_chunk():
    from src.notifier import DeliveryError, deliver_event
    from src.outbox import (
        build_event,
        make_destination_id,
        make_item,
        parse_issue_body,
        render_issue_body,
    )

    webhook_url = "https://hooks.example/wechat_work"
    items = (
        make_item("news", "https://www.anthropic.com/news/a"),
        make_item("news", "https://www.anthropic.com/news/b"),
    )
    event = replace(build_event(
        "news",
        items,
        [{
            "target": "wechat_work",
            "destination_id": make_destination_id(webhook_url),
            "formatter_version": 1,
            "item_ids": [item.item_id],
            "payload": {"part": index + 1},
        } for index, item in enumerate(items)],
        created_at="2026-08-02T00:00:00Z",
    ), issue_number=101)
    attempts = []
    module = MagicMock(FORMATTER_VERSION=1)

    def send(payload, _webhook_url):
        attempts.append(payload["part"])
        if payload["part"] == 2 and attempts.count(2) == 1:
            raise RuntimeError("transient failure")

    module.send.side_effect = send
    formatter = {"name": "wechat_work", "module": module, "webhook_url": webhook_url}
    durable = {"body": render_issue_body(event)}

    def save(value):
        durable["body"] = render_issue_body(value)
        return parse_issue_body(durable["body"], issue_number=101)

    with pytest.raises(DeliveryError):
        deliver_event(event, [formatter], save_event=save)

    restarted = parse_issue_body(durable["body"], issue_number=101)
    completed = deliver_event(restarted, [formatter], save_event=save)

    assert attempts == [1, 2, 2]
    assert completed.status == "delivered"


@patch("src.main.sitemap")
@patch("src.main.detector")
@patch("src.main.issues")
@patch("src.main.notifier")
def test_main_repairs_pending_baseline_before_delivery_even_if_sitemap_fails(
    mock_notifier, mock_issues, mock_detector, mock_sitemap
):
    from src.main import run

    event = _pending_event()
    order = []
    mock_issues.list_pending_events.return_value = [event]
    mock_notifier.discover_formatters.return_value = [{"name": "wechat_work"}]
    mock_detector.ensure_event_in_baseline.side_effect = lambda value: order.append("baseline")
    mock_notifier.deliver_event.side_effect = lambda *args, **kwargs: order.append("delivery") or event
    mock_sitemap.fetch_sitemap.side_effect = lambda: order.append("sitemap") or (_ for _ in ()).throw(
        RuntimeError("sitemap unavailable")
    )

    with pytest.raises(RuntimeError, match="sitemap unavailable"):
        run()

    assert order == ["baseline", "delivery", "sitemap"]
