"""Tests for src/formatters/wechat_work.py — news card format with enriched data."""

import pytest
from unittest.mock import patch, MagicMock


class TestFormatMessage:
    """Tests for format_message() — news type."""

    def test_single_article_with_full_metadata(self):
        from src.formatters.wechat_work import format_message

        changes = {
            "news": [
                {
                    "url": "https://www.anthropic.com/news/claude-opus-4-7",
                    "title": "Introducing Claude Opus 4.7",
                    "description": "Our latest model with improved reasoning.",
                    "image": "https://cdn.sanity.io/images/test/image.png",
                },
            ],
        }

        payload = format_message(changes)

        assert payload["msgtype"] == "news"
        articles = payload["news"]["articles"]
        assert len(articles) == 1
        assert articles[0]["title"] == "Introducing Claude Opus 4.7"
        assert articles[0]["url"] == "https://www.anthropic.com/news/claude-opus-4-7"
        assert articles[0]["picurl"] == "https://cdn.sanity.io/images/test/image.png"

    def test_multiple_categories(self):
        from src.formatters.wechat_work import format_message

        changes = {
            "news": [
                {"url": "https://www.anthropic.com/news/a", "title": "Article A", "description": None, "image": None},
            ],
            "research": [
                {"url": "https://www.anthropic.com/research/b", "title": "Paper B", "description": "A study.", "image": "https://img/b.png"},
            ],
        }

        payload = format_message(changes)

        articles = payload["news"]["articles"]
        assert len(articles) == 2
        titles = [a["title"] for a in articles]
        assert "Article A" in titles
        assert "Paper B" in titles

    def test_truncates_to_8_articles(self):
        from src.formatters.wechat_work import format_message

        changes = {
            "news": [
                {"url": f"https://www.anthropic.com/news/{i}", "title": f"Article {i}", "description": None, "image": None}
                for i in range(10)
            ],
        }

        payload = format_message(changes)

        articles = payload["news"]["articles"]
        assert len(articles) == 8

    def test_empty_changes_returns_none(self):
        from src.formatters.wechat_work import format_message

        result = format_message({})

        assert result is None

    def test_no_image_omits_picurl(self):
        from src.formatters.wechat_work import format_message

        changes = {
            "news": [
                {"url": "https://www.anthropic.com/news/a", "title": "A", "description": None, "image": None},
            ],
        }

        payload = format_message(changes)
        article = payload["news"]["articles"][0]
        assert article.get("picurl", "") == ""

    def test_description_in_article(self):
        from src.formatters.wechat_work import format_message

        changes = {
            "news": [
                {"url": "https://example.com/a", "title": "Title", "description": "Some desc.", "image": None},
            ],
        }

        payload = format_message(changes)
        article = payload["news"]["articles"][0]
        assert "Some desc." in article["description"]


class TestSend:
    """Tests for send()."""

    @patch("src.formatters.wechat_work.requests.post")
    def test_posts_to_webhook_url(self, mock_post):
        from src.formatters.wechat_work import send

        mock_post.return_value = MagicMock(status_code=200)
        mock_post.return_value.raise_for_status = MagicMock()
        payload = {"msgtype": "news", "news": {"articles": []}}

        send(payload, "https://example.com/webhook")

        mock_post.assert_called_once()
        assert mock_post.call_args[0][0] == "https://example.com/webhook"

    @patch("src.formatters.wechat_work.requests.post")
    def test_raises_on_http_error(self, mock_post):
        from src.formatters.wechat_work import send

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("500 Server Error")
        mock_post.return_value = mock_response

        with pytest.raises(Exception):
            send({"msgtype": "news"}, "https://example.com")
