"""DingTalk webhook formatter — markdown message with HMAC-SHA256 signing."""

import base64
import hashlib
import hmac
import os
import time
from urllib.parse import quote_plus, urlparse

import requests


def _compute_sign(timestamp: int, secret: str) -> str:
    """Compute HMAC-SHA256 signature for DingTalk webhook."""
    string_to_sign = f"{timestamp}\n{secret}"
    hmac_code = hmac.new(
        secret.encode("utf-8"),
        string_to_sign.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    return quote_plus(base64.b64encode(hmac_code).decode("utf-8"))


def format_message(changes: dict[str, list[dict]]) -> dict | None:
    """Format enriched changes into a DingTalk markdown message payload."""
    if not changes:
        return None

    lines = ["## Anthropic Website Update\n"]

    for category, items in sorted(changes.items()):
        if not items:
            continue
        lines.append(f"**{category.capitalize()}**:\n")
        for item in items:
            title = item["title"]
            url = item["url"]
            lines.append(f"- [{title}]({url})")
        lines.append("")

    text = "\n".join(lines)

    return {
        "msgtype": "markdown",
        "markdown": {
            "title": "Anthropic Website Update",
            "text": text,
        },
    }


def send(payload: dict, webhook_url: str) -> None:
    """Send payload to DingTalk webhook, with optional HMAC signing."""
    secret = os.environ.get("DINGTALK_SECRET")

    if secret:
        timestamp = int(time.time() * 1000)
        sign = _compute_sign(timestamp, secret)
        webhook_url = f"{webhook_url}&timestamp={timestamp}&sign={sign}"

    response = requests.post(webhook_url, json=payload, timeout=10)
    response.raise_for_status()
