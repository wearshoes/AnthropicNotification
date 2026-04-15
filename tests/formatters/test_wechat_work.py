"""Tests for src/formatters/wechat_work.py — written BEFORE implementation."""

import pytest
from unittest.mock import patch, MagicMock


class TestFormatMessage:
    """Tests for format_message()."""

    def test_formats_single_category(self):
        from src.formatters.wechat_work import format_message

        changes = {
            "news": {"https://www.anthropic.com/news/project-glasswing"},
        }

        payload = format_message(changes)

        assert payload["msgtype"] == "markdown"
        assert "project-glasswing" in payload["markdown"]["content"]
        assert "news" in payload["markdown"]["content"].lower()

    def test_formats_multiple_categories(self):
        from src.formatters.wechat_work import format_message

        changes = {
            "news": {"https://www.anthropic.com/news/a"},
            "research": {"https://www.anthropic.com/research/b"},
        }

        payload = format_message(changes)

        content = payload["markdown"]["content"]
        assert "news" in content.lower()
        assert "research" in content.lower()

    def test_truncates_when_exceeds_4096_bytes(self):
        from src.formatters.wechat_work import format_message

        # Generate enough URLs to exceed 4096 bytes
        changes = {
            "news": {f"https://www.anthropic.com/news/very-long-article-name-{i:04d}" for i in range(100)},
        }

        payload = format_message(changes)

        content_bytes = payload["markdown"]["content"].encode("utf-8")
        assert len(content_bytes) <= 4096

    def test_empty_changes_returns_none(self):
        from src.formatters.wechat_work import format_message

        result = format_message({})

        assert result is None


class TestSend:
    """Tests for send()."""

    @patch("src.formatters.wechat_work.requests.post")
    def test_posts_to_webhook_url(self, mock_post):
        from src.formatters.wechat_work import send

        mock_post.return_value = MagicMock(status_code=200)
        payload = {"msgtype": "markdown", "markdown": {"content": "test"}}

        send(payload, "https://example.com/webhook")

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://example.com/webhook"
        assert call_args[1]["json"] == payload

    @patch("src.formatters.wechat_work.requests.post")
    def test_raises_on_http_error(self, mock_post):
        from src.formatters.wechat_work import send

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("500 Server Error")
        mock_post.return_value = mock_response

        with pytest.raises(Exception):
            send({"msgtype": "markdown", "markdown": {"content": "test"}}, "https://example.com")
