"""Tests for src/formatters/dingtalk.py — written BEFORE implementation."""

import pytest
from unittest.mock import patch, MagicMock


class TestFormatMessage:
    """Tests for format_message()."""

    def test_formats_single_category(self):
        from src.formatters.dingtalk import format_message

        changes = {
            "news": {"https://www.anthropic.com/news/project-glasswing"},
        }

        payload = format_message(changes)

        assert payload["msgtype"] == "markdown"
        assert "title" in payload["markdown"]
        assert "text" in payload["markdown"]
        assert "project-glasswing" in payload["markdown"]["text"]

    def test_formats_multiple_categories(self):
        from src.formatters.dingtalk import format_message

        changes = {
            "news": {"https://www.anthropic.com/news/a"},
            "research": {"https://www.anthropic.com/research/b"},
        }

        payload = format_message(changes)

        text = payload["markdown"]["text"]
        assert "news" in text.lower()
        assert "research" in text.lower()

    def test_empty_changes_returns_none(self):
        from src.formatters.dingtalk import format_message

        result = format_message({})

        assert result is None

    def test_title_is_summary(self):
        from src.formatters.dingtalk import format_message

        changes = {"news": {"https://www.anthropic.com/news/a"}}

        payload = format_message(changes)

        assert payload["markdown"]["title"]  # non-empty title


class TestSend:
    """Tests for send()."""

    @patch("src.formatters.dingtalk.requests.post")
    @patch.dict("os.environ", {"DINGTALK_SECRET": "test_secret"})
    def test_signs_request_with_hmac(self, mock_post):
        from src.formatters.dingtalk import send

        mock_post.return_value = MagicMock(status_code=200)
        mock_post.return_value.raise_for_status = MagicMock()
        payload = {"msgtype": "markdown", "markdown": {"title": "t", "text": "t"}}

        send(payload, "https://oapi.dingtalk.com/robot/send?access_token=xxx")

        called_url = mock_post.call_args[0][0]
        assert "timestamp=" in called_url
        assert "sign=" in called_url

    @patch("src.formatters.dingtalk.requests.post")
    @patch.dict("os.environ", {}, clear=True)
    def test_sends_without_signing_when_no_secret(self, mock_post):
        from src.formatters.dingtalk import send

        mock_post.return_value = MagicMock(status_code=200)
        mock_post.return_value.raise_for_status = MagicMock()
        payload = {"msgtype": "markdown", "markdown": {"title": "t", "text": "t"}}

        send(payload, "https://oapi.dingtalk.com/robot/send?access_token=xxx")

        called_url = mock_post.call_args[0][0]
        assert called_url == "https://oapi.dingtalk.com/robot/send?access_token=xxx"

    @patch("src.formatters.dingtalk.requests.post")
    @patch.dict("os.environ", {}, clear=True)
    def test_posts_correct_payload(self, mock_post):
        from src.formatters.dingtalk import send

        mock_post.return_value = MagicMock(status_code=200)
        mock_post.return_value.raise_for_status = MagicMock()
        payload = {"msgtype": "markdown", "markdown": {"title": "t", "text": "t"}}

        send(payload, "https://example.com/webhook")

        assert mock_post.call_args[1]["json"] == payload

    @patch("src.formatters.dingtalk.requests.post")
    @patch.dict("os.environ", {}, clear=True)
    def test_raises_on_http_error(self, mock_post):
        from src.formatters.dingtalk import send

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("500 Server Error")
        mock_post.return_value = mock_response

        with pytest.raises(Exception):
            send({"msgtype": "markdown", "markdown": {"title": "t", "text": "t"}}, "https://example.com")


class TestSignature:
    """Tests for _compute_sign() helper."""

    def test_signature_is_deterministic(self):
        from src.formatters.dingtalk import _compute_sign

        sign1 = _compute_sign(1234567890000, "test_secret")
        sign2 = _compute_sign(1234567890000, "test_secret")

        assert sign1 == sign2
        assert len(sign1) > 0

    def test_different_timestamps_produce_different_signs(self):
        from src.formatters.dingtalk import _compute_sign

        sign1 = _compute_sign(1234567890000, "test_secret")
        sign2 = _compute_sign(1234567890001, "test_secret")

        assert sign1 != sign2
