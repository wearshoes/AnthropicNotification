"""Tests for the DingTalk formatter."""

from unittest.mock import patch


def _changes():
    return {
        "news": [{
            "url": "https://www.anthropic.com/news/a",
            "title": "Article A",
            "description": None,
            "image": None,
        }]
    }


class TestFormatMessage:
    def test_formats_markdown(self):
        from src.formatters.dingtalk import format_message

        payload = format_message(_changes())
        assert payload["msgtype"] == "markdown"
        assert "Article A" in payload["markdown"]["text"]
        assert payload["markdown"]["title"]

    def test_multiple_categories(self):
        from src.formatters.dingtalk import format_message

        changes = _changes()
        changes["research"] = [{
            "url": "https://www.anthropic.com/research/b",
            "title": "Paper B",
            "description": None,
            "image": None,
        }]
        text = format_message(changes)["markdown"]["text"].lower()
        assert "news" in text and "research" in text

    def test_empty_changes_returns_none(self):
        from src.formatters.dingtalk import format_message

        assert format_message({}) is None


class TestSend:
    @patch("src.formatters.dingtalk.post_json")
    @patch.dict("os.environ", {"DINGTALK_SECRET": "test_secret"})
    def test_signs_request_with_hmac(self, mock_post):
        from src.formatters.dingtalk import send

        payload = {"msgtype": "markdown"}
        send(payload, "https://oapi.dingtalk.com/robot/send?access_token=xxx")
        called_url = mock_post.call_args.args[0]
        assert "timestamp=" in called_url and "sign=" in called_url
        assert mock_post.call_args.args[1] == payload

    @patch("src.formatters.dingtalk.post_json")
    @patch.dict("os.environ", {}, clear=True)
    def test_sends_without_signing_when_no_secret(self, mock_post):
        from src.formatters.dingtalk import send

        payload = {"msgtype": "markdown"}
        url = "https://example.com/webhook"
        send(payload, url)
        mock_post.assert_called_once_with(url, payload)


class TestSignature:
    def test_signature_is_deterministic(self):
        from src.formatters.dingtalk import _compute_sign

        assert _compute_sign(1234567890000, "secret") == _compute_sign(1234567890000, "secret")

    def test_different_timestamps_change_signature(self):
        from src.formatters.dingtalk import _compute_sign

        assert _compute_sign(1, "secret") != _compute_sign(2, "secret")
