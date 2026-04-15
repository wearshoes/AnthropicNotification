"""
Formatter Test Template — Reference test patterns for new notification platforms.

To create tests for a new formatter:
1. Copy this file to tests/formatters/test_<platform_name>.py
2. Replace '_template' imports with your platform module name
3. Adjust assertions for your platform's specific payload format
4. Add platform-specific tests (e.g., signing, rate limits)

Tests MUST be written BEFORE the implementation (TDD RED phase).
"""

import pytest
from unittest.mock import patch, MagicMock


# ============================================================
# Tests for format_message()
# ============================================================

class TestFormatMessage:

    def test_formats_single_category(self):
        # from src.formatters.<platform> import format_message
        from src.formatters._template import format_message

        changes = {
            "news": {"https://www.anthropic.com/news/project-glasswing"},
        }

        payload = format_message(changes)

        # Adjust these assertions for your platform's payload format:
        assert payload is not None
        # Example for markdown-based platforms:
        assert "project-glasswing" in str(payload)
        assert "news" in str(payload).lower()

    def test_formats_multiple_categories(self):
        from src.formatters._template import format_message

        changes = {
            "news": {"https://www.anthropic.com/news/a"},
            "research": {"https://www.anthropic.com/research/b"},
        }

        payload = format_message(changes)

        content = str(payload)
        assert "news" in content.lower()
        assert "research" in content.lower()

    def test_empty_changes_returns_none(self):
        from src.formatters._template import format_message

        result = format_message({})

        assert result is None

    # --- Platform-specific tests to add: ---
    #
    # def test_truncates_when_exceeds_size_limit(self):
    #     """If your platform has a message size limit (e.g., 4096 bytes for WeChat Work)."""
    #     ...
    #
    # def test_includes_required_fields(self):
    #     """If your platform requires specific fields (e.g., 'title' for DingTalk)."""
    #     ...


# ============================================================
# Tests for send()
# ============================================================

class TestSend:

    # Replace 'src.formatters._template.requests.post' with your module path
    @patch("src.formatters._template.requests.post")
    def test_posts_to_webhook_url(self, mock_post):
        from src.formatters._template import send

        mock_post.return_value = MagicMock(status_code=200)
        payload = {"msgtype": "markdown", "markdown": {"content": "test"}}

        send(payload, "https://example.com/webhook")

        mock_post.assert_called_once()
        assert mock_post.call_args[0][0] == "https://example.com/webhook"
        assert mock_post.call_args[1]["json"] == payload

    @patch("src.formatters._template.requests.post")
    def test_raises_on_http_error(self, mock_post):
        from src.formatters._template import send

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("500 Server Error")
        mock_post.return_value = mock_response

        with pytest.raises(Exception):
            send({"test": True}, "https://example.com")

    # --- Platform-specific tests to add: ---
    #
    # def test_signs_request_with_hmac(self):
    #     """If your platform requires HMAC-SHA256 signing (DingTalk, Feishu)."""
    #     ...
    #
    # def test_includes_timestamp_in_signed_request(self):
    #     """If signing requires a timestamp parameter."""
    #     ...
