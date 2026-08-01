"""DingTalk markdown formatter with optional HMAC-SHA256 signing."""

import base64
import hashlib
import hmac
import os
import time
from urllib.parse import quote_plus

from src.webhook_http import post_json


FORMATTER_VERSION = 1
MAX_ITEMS_PER_MESSAGE = 20


def _compute_sign(timestamp: int, secret: str) -> str:
    """Compute DingTalk's HMAC-SHA256 signature."""
    string_to_sign = f"{timestamp}\n{secret}"
    digest = hmac.new(
        secret.encode("utf-8"),
        string_to_sign.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    return quote_plus(base64.b64encode(digest).decode("utf-8"))


def format_message(changes: dict[str, list[dict]]) -> dict | None:
    """Format one bounded chunk as DingTalk markdown."""
    if not changes:
        return None
    lines = ["## Anthropic Website Update\n"]
    item_count = 0
    for category, items in sorted(changes.items()):
        if not items:
            continue
        lines.append(f"**{category.capitalize()}**:\n")
        for item in items:
            lines.append(f"- [{item['title']}]({item['url']})")
            item_count += 1
        lines.append("")
    if item_count == 0:
        return None
    return {
        "msgtype": "markdown",
        "markdown": {
            "title": "Anthropic Website Update",
            "text": "\n".join(lines),
        },
    }


def send(payload: dict, webhook_url: str) -> None:
    """Sign if configured, then require DingTalk business success."""
    secret = os.environ.get("DINGTALK_SECRET")
    if secret:
        timestamp = int(time.time() * 1000)
        separator = "&" if "?" in webhook_url else "?"
        webhook_url = (
            f"{webhook_url}{separator}timestamp={timestamp}"
            f"&sign={_compute_sign(timestamp, secret)}"
        )
    post_json(webhook_url, payload)
