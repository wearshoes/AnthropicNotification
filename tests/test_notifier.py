"""Tests for formatter discovery and durable notifier contracts."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch


class TestDiscoverFormatters:
    @patch.dict(os.environ, {"WECHAT_WORK_WEBHOOK": "https://example.com/hook"}, clear=False)
    @patch("src.notifier.importlib.import_module")
    @patch("src.notifier.FORMATTERS_DIR")
    def test_loads_formatter_when_env_var_exists(self, mock_dir, mock_import):
        from src.notifier import discover_formatters

        mock_dir.glob.return_value = [Path("src/formatters/wechat_work.py")]
        mock_import.return_value = MagicMock()
        assert [item["name"] for item in discover_formatters()] == ["wechat_work"]

    @patch.dict(os.environ, {}, clear=True)
    def test_skips_formatter_without_webhook(self):
        from src.notifier import discover_formatters

        assert discover_formatters() == []

    @patch.dict(
        os.environ,
        {
            "WECHAT_WORK_WEBHOOK": "https://example.com/hook",
            "WECHAT_WORK_ENABLED": "false",
        },
        clear=False,
    )
    def test_skips_explicitly_disabled_formatter(self):
        from src.notifier import discover_formatters

        assert "wechat_work" not in [item["name"] for item in discover_formatters()]

    @patch.dict(os.environ, {"WECHAT_WORK_WEBHOOK": "https://example.com/hook"}, clear=False)
    @patch("src.notifier.importlib.import_module", side_effect=ImportError("broken"))
    @patch("src.notifier.FORMATTERS_DIR")
    def test_configured_broken_formatter_fails_closed(self, mock_dir, mock_import):
        import pytest
        from src.notifier import FormatterPlanningError, discover_formatters

        mock_dir.glob.return_value = [Path("src/formatters/wechat_work.py")]
        with pytest.raises(FormatterPlanningError, match="wechat_work"):
            discover_formatters()
