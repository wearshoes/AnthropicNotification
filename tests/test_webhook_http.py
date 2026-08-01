"""Tests for bounded webhook retries and business response validation."""

from unittest.mock import MagicMock, patch

import pytest


@patch("src.webhook_http.time.sleep")
@patch("src.webhook_http.requests.post")
def test_http_200_business_error_retries_and_raises(mock_post, mock_sleep):
    from src.webhook_http import WebhookDeliveryError, post_json

    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"errcode": 40014, "errmsg": "invalid access token"}
    mock_post.return_value = response

    with pytest.raises(WebhookDeliveryError, match="errcode=40014"):
        post_json("https://hooks.example/redacted", {"msgtype": "news"})

    assert mock_post.call_count == 3
    assert mock_sleep.call_count == 2


@patch("src.webhook_http.requests.post")
def test_http_200_success_code_returns_response(mock_post):
    from src.webhook_http import post_json

    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"errcode": 0, "errmsg": "ok"}
    mock_post.return_value = response

    assert post_json("https://hooks.example/redacted", {"ok": True}) == {"errcode": 0, "errmsg": "ok"}
    assert mock_post.call_count == 1


@patch("src.webhook_http.requests.post")
def test_webhook_redirect_is_not_followed_or_receipted(mock_post):
    from src.webhook_http import WebhookDeliveryError, post_json

    response = MagicMock()
    response.status_code = 307
    response.json.return_value = {"errcode": 0}
    mock_post.return_value = response

    with pytest.raises(WebhookDeliveryError, match="HTTP status 307"):
        post_json("https://hooks.example/redacted", {"ok": True}, attempts=1)

    mock_post.assert_called_once_with(
        "https://hooks.example/redacted",
        json={"ok": True},
        timeout=10,
        allow_redirects=False,
    )
