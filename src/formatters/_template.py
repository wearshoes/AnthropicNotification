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


def format_message(changes: dict[str, set[str]]) -> dict | None:
    """Format detected changes into a platform-specific message payload.

    Args:
        changes: Dict mapping category name to set of new URLs.
                 Example: {"news": {"https://www.anthropic.com/news/article-1"},
                           "research": {"https://www.anthropic.com/research/paper-1"}}

    Returns:
        Platform-specific payload dict ready to POST, or None if nothing to send.

    Notes:
        - Multiple categories may have updates in a single run
        - URLs are the only guaranteed data; title/date are NOT available
        - The slug (last path segment) can be used as a display name
        - Check your platform's message size limits and truncate accordingly
    """
    if not changes:
        return None

    # --- Build message content ---
    lines = []
    for category, urls in sorted(changes.items()):
        if not urls:
            continue
        lines.append(f"**{category.capitalize()}**:")
        for url in sorted(urls):
            slug = urlparse(url).path.rstrip("/").split("/")[-1]
            lines.append(f"  - [{slug}]({url})")

    content = "\n".join(lines)

    # --- Build platform-specific payload ---
    # Replace this with your platform's expected format:
    #
    #   WeChat Work: {"msgtype": "markdown", "markdown": {"content": ...}}
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
