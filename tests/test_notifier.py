"""Tests for src/notifier.py — written BEFORE implementation."""

import pytest
from unittest.mock import patch, MagicMock
import importlib
import os


class TestDiscoverFormatters:
    """Tests for discover_formatters() — convention-based discovery."""

    @patch.dict(os.environ, {"WECHAT_WORK_WEBHOOK": "https://example.com/hook"}, clear=False)
    @patch("src.notifier.importlib.import_module")
    @patch("src.notifier.FORMATTERS_DIR")
    def test_loads_formatter_when_env_var_exists(self, mock_dir, mock_import):
        from src.notifier import discover_formatters
        from pathlib import Path

        # Simulate wechat_work.py existing in formatters dir
        mock_dir.glob.return_value = [Path("src/formatters/wechat_work.py")]

        mock_module = MagicMock()
        mock_module.format_message = MagicMock()
        mock_module.send = MagicMock()
        mock_import.return_value = mock_module

        formatters = discover_formatters()

        found_names = [f["name"] for f in formatters]
        assert "wechat_work" in found_names

    @patch.dict(os.environ, {}, clear=True)
    def test_skips_formatter_when_no_env_var(self):
        from src.notifier import discover_formatters

        # With no env vars at all, no formatters should be enabled
        formatters = discover_formatters()

        assert len(formatters) == 0

    @patch.dict(os.environ, {"WECHAT_WORK_WEBHOOK": "https://example.com/hook", "WECHAT_WORK_ENABLED": "false"}, clear=False)
    def test_skips_formatter_when_explicitly_disabled(self):
        from src.notifier import discover_formatters

        formatters = discover_formatters()

        found_names = [f["name"] for f in formatters]
        assert "wechat_work" not in found_names


class TestSendNotifications:
    """Tests for send_notifications()."""

    def test_aggregates_and_sends_to_all_formatters(self):
        from src.notifier import send_notifications

        mock_formatter = {
            "name": "test_platform",
            "module": MagicMock(),
            "webhook_url": "https://example.com/hook",
        }
        mock_formatter["module"].format_message.return_value = {"msg": "test"}
        mock_formatter["module"].send.return_value = None

        changes = {
            "news": {"https://www.anthropic.com/news/a"},
            "research": {"https://www.anthropic.com/research/b"},
        }

        send_notifications([mock_formatter], changes)

        mock_formatter["module"].format_message.assert_called_once_with(changes)
        mock_formatter["module"].send.assert_called_once_with({"msg": "test"}, "https://example.com/hook")

    def test_one_failure_does_not_block_others(self):
        from src.notifier import send_notifications

        failing_formatter = {
            "name": "failing",
            "module": MagicMock(),
            "webhook_url": "https://fail.com",
        }
        failing_formatter["module"].format_message.side_effect = Exception("boom")

        passing_formatter = {
            "name": "passing",
            "module": MagicMock(),
            "webhook_url": "https://pass.com",
        }
        passing_formatter["module"].format_message.return_value = {"ok": True}
        passing_formatter["module"].send.return_value = None

        changes = {"news": {"https://www.anthropic.com/news/a"}}

        # Should not raise
        send_notifications([failing_formatter, passing_formatter], changes)

        # Passing formatter should still have been called
        passing_formatter["module"].send.assert_called_once()

    def test_empty_changes_skips_notifications(self):
        from src.notifier import send_notifications

        mock_formatter = {
            "name": "test",
            "module": MagicMock(),
            "webhook_url": "https://example.com",
        }

        send_notifications([mock_formatter], {})

        mock_formatter["module"].format_message.assert_not_called()
