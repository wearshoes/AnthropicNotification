"""Tests for the durable main orchestrator."""

from dataclasses import replace
from unittest.mock import call, patch

import pytest


def _event():
    from src.outbox import build_event, make_destination_id, make_item

    item = make_item("news", "https://www.anthropic.com/news/a")
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


class TestFinalization:
    @patch("src.main.notifier")
    @patch("src.main.issues")
    def test_cleanup_finishes_before_pending_label_is_removed(
        self, mock_issues, mock_notifier
    ):
        from src.main import _deliver_and_finalize
        from src.outbox import record_receipt

        event = _event()
        delivered = record_receipt(event, event.chunks[0].chunk_id)
        mock_notifier.deliver_event.return_value = delivered

        _deliver_and_finalize(event, [{"name": "wechat_work"}])

        assert mock_issues.method_calls == [
            call.close_old_update_issues("news", exclude_number=101),
            call.finalize_outbox_event(delivered),
        ]

    @patch("src.main.notifier")
    @patch("src.main.issues")
    def test_cleanup_failure_leaves_event_pending(self, mock_issues, mock_notifier):
        from src.main import _deliver_and_finalize
        from src.outbox import record_receipt

        event = _event()
        delivered = record_receipt(event, event.chunks[0].chunk_id)
        mock_notifier.deliver_event.return_value = delivered
        mock_issues.close_old_update_issues.side_effect = RuntimeError("cleanup failed")

        with pytest.raises(RuntimeError, match="cleanup failed"):
            _deliver_and_finalize(event, [{"name": "wechat_work"}])

        mock_issues.finalize_outbox_event.assert_not_called()


class TestRun:
    @patch("src.main.notifier")
    @patch("src.main.detector")
    @patch("src.main.issues")
    @patch("src.main.sitemap")
    def test_full_flow_delivers_each_new_event(
        self, mock_sitemap, mock_issues, mock_detector, mock_notifier
    ):
        from src.main import run
        from src.outbox import record_receipt

        event = _event()
        delivered = record_receipt(event, event.chunks[0].chunk_id)
        mock_issues.list_pending_events.return_value = []
        mock_sitemap.fetch_sitemap.return_value = [{"loc": event.items[0].url}]
        mock_sitemap.filter_by_category.return_value = {
            "news": {event.items[0].url}, "research": set(),
            "engineering": set(), "learn": set(),
        }
        mock_detector.process_category.side_effect = [[event], [], [], []]
        mock_notifier.discover_formatters.return_value = [{"name": "wechat_work"}]
        mock_notifier.deliver_event.return_value = delivered

        run()

        assert mock_detector.process_category.call_count == 4
        mock_notifier.deliver_event.assert_called_once()
        mock_issues.finalize_outbox_event.assert_called_once_with(delivered)

    @patch("src.main.notifier")
    @patch("src.main.detector")
    @patch("src.main.issues")
    @patch("src.main.sitemap")
    def test_no_changes_attempts_all_categories(
        self, mock_sitemap, mock_issues, mock_detector, mock_notifier
    ):
        from src.main import run

        mock_issues.list_pending_events.return_value = []
        mock_sitemap.fetch_sitemap.return_value = []
        mock_sitemap.filter_by_category.return_value = {
            "news": set(), "research": set(), "engineering": set(), "learn": set()
        }
        mock_detector.process_category.return_value = []
        mock_notifier.discover_formatters.return_value = []
        run()
        assert mock_detector.process_category.call_count == 4

    @patch("src.main.notifier")
    @patch("src.main.issues")
    @patch("src.main.sitemap")
    def test_sitemap_error_raises_after_pending_query(
        self, mock_sitemap, mock_issues, mock_notifier
    ):
        from src.main import run

        mock_issues.list_pending_events.return_value = []
        mock_notifier.discover_formatters.return_value = []
        mock_sitemap.fetch_sitemap.side_effect = RuntimeError("network error")
        with pytest.raises(RuntimeError, match="network error"):
            run()


class TestDryRun:
    @patch("src.main.issues")
    @patch("src.main.notifier")
    @patch("src.main.detector")
    @patch("src.main.sitemap")
    def test_dry_run_has_no_state_calls(
        self, mock_sitemap, mock_detector, mock_notifier, mock_issues
    ):
        from src.main import run

        categorized = {"news": {"https://www.anthropic.com/news/a"}}
        mock_sitemap.fetch_sitemap.return_value = []
        mock_sitemap.filter_by_category.return_value = categorized
        assert run(dry_run=True) == categorized
        mock_issues.list_pending_events.assert_not_called()
        mock_detector.process_category.assert_not_called()
