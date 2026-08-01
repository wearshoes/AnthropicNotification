"""Tests ensuring webhook credentials never escape through error text."""

from unittest.mock import MagicMock, patch

import pytest
import requests


@patch("src.webhook_http.requests.post")
def test_transport_error_does_not_expose_webhook_url_or_token(mock_post):
    from src.webhook_http import WebhookDeliveryError, post_json

    secret_url = "https://hooks.example/send?access_token=super-secret-token"
    mock_post.side_effect = requests.ConnectionError(
        f"connection failed for {secret_url}"
    )

    with pytest.raises(WebhookDeliveryError) as raised:
        post_json(secret_url, {"ok": True}, attempts=1)

    message = str(raised.value)
    assert secret_url not in message
    assert "super-secret-token" not in message
    assert "ConnectionError" in message


@patch("src.webhook_http.requests.post")
def test_business_error_does_not_expose_remote_error_text(mock_post):
    from src.webhook_http import WebhookDeliveryError, post_json

    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "errcode": 40001,
        "errmsg": "invalid webhook https://hooks.example/send?key=TOPSECRET",
    }
    mock_post.return_value = response

    with pytest.raises(WebhookDeliveryError) as raised:
        post_json("https://hooks.example/send?key=TOPSECRET", {"ok": True}, attempts=1)

    message = str(raised.value)
    assert "TOPSECRET" not in message
    assert "https://" not in message
    assert "errcode=40001" in message


@pytest.mark.parametrize(
    "untrusted_errcode",
    [
        "https://hooks.example/send?key=TOPSECRET",
        "40001",
        "0",
        0.0,
        True,
        False,
        10**20,
    ],
)
@patch("src.webhook_http.requests.post")
def test_business_error_only_exposes_bounded_integer_code(
    mock_post, untrusted_errcode
):
    from src.webhook_http import WebhookDeliveryError, post_json

    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"errcode": untrusted_errcode}
    mock_post.return_value = response

    with pytest.raises(WebhookDeliveryError) as raised:
        post_json("https://hooks.example/send?key=TOPSECRET", {"ok": True}, attempts=1)

    message = str(raised.value)
    assert message == "webhook rejected request: errcode=unknown"
    assert "TOPSECRET" not in message
