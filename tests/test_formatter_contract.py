"""Tests for explicit formatter versions and fixed destination identity."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


@patch("src.notifier.enrich_urls")
def test_planning_rejects_formatter_without_explicit_version(mock_enrich):
    from src.notifier import FormatterPlanningError, plan_event

    url = "https://www.anthropic.com/news/a"
    mock_enrich.return_value = {
        "news": [{"url": url, "title": "A", "description": None, "image": None}]
    }
    module = SimpleNamespace(
        MAX_ITEMS_PER_MESSAGE=8,
        format_message=lambda changes: {"ok": True},
        send=lambda payload, webhook_url: None,
    )

    with pytest.raises(FormatterPlanningError, match="FORMATTER_VERSION"):
        plan_event("news", {url}, [{
            "name": "invalid",
            "module": module,
            "webhook_url": "https://hooks.example/one",
        }])


@patch("src.notifier.enrich_urls")
def test_pending_event_rejects_changed_destination(mock_enrich):
    from src.notifier import DeliveryError, deliver_event, plan_event

    url = "https://www.anthropic.com/news/a"
    mock_enrich.return_value = {
        "news": [{"url": url, "title": "A", "description": None, "image": None}]
    }
    module = MagicMock(FORMATTER_VERSION=1, MAX_ITEMS_PER_MESSAGE=8)
    module.FORMATTER_VERSION = 1
    module.MAX_ITEMS_PER_MESSAGE = 8
    module.format_message.return_value = {"ok": True}
    original = {"name": "target", "module": module, "webhook_url": "https://hooks.example/one"}
    changed = {"name": "target", "module": module, "webhook_url": "https://hooks.example/two"}
    event = plan_event("news", {url}, [original])

    with pytest.raises(DeliveryError, match="destination"):
        deliver_event(event, [changed], save_event=lambda value: value)
    module.send.assert_not_called()
