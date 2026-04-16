"""
Formatter Template — Reference implementation for new notification platforms.

To create a new formatter:
1. Copy this file to src/formatters/<platform_name>.py
2. Implement format_message() and send()
3. Add <PLATFORM_NAME>_WEBHOOK to GitHub Secrets
4. Add env line to .github/workflows/monitor.yml

The system discovers formatters by convention:
  filename: my_platform.py  →  env var: MY_PLATFORM_WEBHOOK

This file starts with '_' so it won't be loaded by the notifier.
"""

from urllib.parse import urlparse

import requests


def format_message(changes: dict[str, list[dict]]) -> dict | None:
    """Format detected changes into a platform-specific message payload.

    Args:
        changes: Dict mapping category name to list of enriched dicts.
                 Each dict has: url, title, description (or None), image (or None).
                 Example: {"news": [
                     {"url": "https://...", "title": "Article Title",
                      "description": "Summary text.", "image": "https://...png"},
                 ]}

    Returns:
        Platform-specific payload dict ready to POST, or None if nothing to send.

    Notes:
        - Multiple categories may have updates in a single run
        - Each item has: url, title, description (may be None), image (may be None)
        - title is extracted from og:title or falls back to URL slug
        - Check your platform's message size limits and truncate accordingly
    """
    if not changes:
        return None

    # --- Build message content ---
    lines = []
    for category, items in sorted(changes.items()):
        if not items:
            continue
        lines.append(f"**{category.capitalize()}**:")
        for item in items:
            lines.append(f"  - [{item['title']}]({item['url']})")

    content = "\n".join(lines)

    # --- Build platform-specific payload ---
    # Replace this with your platform's expected format:
    #
    #   WeChat Work: {"msgtype": "news", "news": {"articles": [{title, description, url, picurl}]}}
    #   DingTalk:    {"msgtype": "markdown", "markdown": {"title": ..., "text": ...}}
    #   Feishu:      {"msg_type": "interactive", "card": {...}}
    #   Slack:       {"blocks": [...]}
    #   Custom:      {"event": "update", "changes": ...}
    return {
        "msgtype": "markdown",
        "markdown": {
            "content": content,
        },
    }


def send(payload: dict, webhook_url: str) -> None:
    """Send the formatted payload to the webhook endpoint.

    Args:
        payload: The dict returned by format_message().
        webhook_url: The webhook URL from the environment variable.

    Raises:
        Exception on HTTP errors (the notifier catches and logs these).

    Notes:
        - If your platform requires request signing (DingTalk, Feishu),
          implement the signing logic here.
        - For HMAC-SHA256 signing, the secret comes from env var
          <PLATFORM_NAME>_SECRET (read it with os.environ.get).
        - The notifier will catch any exception, log it, and continue
          with other platforms — so raise on error, don't swallow it.
    """
    response = requests.post(webhook_url, json=payload, timeout=10)
    response.raise_for_status()
