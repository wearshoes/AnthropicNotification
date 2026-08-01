"""Tests for the WeChat Work formatter."""

from unittest.mock import patch


def _changes(count=1):
    return {
        "news": [
            {
                "url": f"https://www.anthropic.com/news/{index}",
                "title": f"Article {index}",
                "description": None,
                "image": None,
            }
            for index in range(count)
        ]
    }


class TestFormatMessage:
    def test_formats_news_payload(self):
        from src.formatters.wechat_work import format_message

        payload = format_message(_changes())
        assert payload["msgtype"] == "news"
        assert payload["news"]["articles"][0]["title"] == "Article 0"

    def test_multiple_categories(self):
        from src.formatters.wechat_work import format_message

        changes = _changes()
        changes["research"] = [{
            "url": "https://www.anthropic.com/research/a",
            "title": "Paper",
            "description": "Study",
            "image": "https://cdn.example/a.png",
        }]
        titles = [item["title"] for item in format_message(changes)["news"]["articles"]]
        assert titles == ["Article 0", "Paper"]

    def test_defensive_limit_is_eight(self):
        from src.formatters.wechat_work import format_message

        assert len(format_message(_changes(10))["news"]["articles"]) == 8

    def test_empty_changes_returns_none(self):
        from src.formatters.wechat_work import format_message

        assert format_message({}) is None

    def test_description_and_image_fallbacks(self):
        from src.formatters.wechat_work import format_message

        article = format_message(_changes())["news"]["articles"][0]
        assert article["description"] == "Category: News"
        assert article["picurl"] == ""


class TestSend:
    @patch("src.formatters.wechat_work.post_json")
    def test_delegates_verified_delivery(self, mock_post):
        from src.formatters.wechat_work import send

        payload = {"msgtype": "news"}
        send(payload, "https://example.com/webhook")
        mock_post.assert_called_once_with("https://example.com/webhook", payload)
