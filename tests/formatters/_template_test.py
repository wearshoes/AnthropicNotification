"""Reference tests to copy when implementing a new formatter."""

from unittest.mock import patch

import pytest


def test_declares_versioned_bounded_formatter_contract():
    from src.formatters import _template

    assert isinstance(_template.FORMATTER_VERSION, int)
    assert _template.FORMATTER_VERSION > 0
    assert isinstance(_template.MAX_ITEMS_PER_MESSAGE, int)
    assert _template.MAX_ITEMS_PER_MESSAGE > 0


class TestFormatMessage:
    def test_formats_single_category(self):
        from src.formatters._template import format_message

        payload = format_message({
            "news": [{
                "url": "https://www.anthropic.com/news/a",
                "title": "Article A",
                "description": None,
                "image": None,
            }]
        })
        assert "Article A" in payload["text"]
        assert "news" in payload["text"].lower()

    def test_formats_multiple_categories(self):
        from src.formatters._template import format_message

        payload = format_message({
            "news": [{"url": "https://example/a", "title": "A"}],
            "research": [{"url": "https://example/b", "title": "B"}],
        })
        assert "News" in payload["text"]
        assert "Research" in payload["text"]

    def test_empty_changes_returns_none(self):
        from src.formatters._template import format_message

        assert format_message({}) is None


class TestSend:
    @patch("src.formatters._template.post_json")
    def test_uses_verified_webhook_delivery(self, mock_post):
        from src.formatters._template import send

        payload = {"text": "test"}
        send(payload, "https://example.com/webhook")
        mock_post.assert_called_once_with("https://example.com/webhook", payload)

    @patch("src.formatters._template.post_json", side_effect=RuntimeError("rejected"))
    def test_propagates_delivery_failure(self, _mock_post):
        from src.formatters._template import send

        with pytest.raises(RuntimeError, match="rejected"):
            send({"text": "test"}, "https://example.com/webhook")
