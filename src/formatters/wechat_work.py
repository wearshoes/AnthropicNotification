"""WeChat Work webhook formatter — markdown message format."""

from urllib.parse import urlparse

import requests

MAX_CONTENT_BYTES = 4096


def format_message(changes: dict[str, set[str]]) -> dict | None:
    """Format changes into a WeChat Work markdown message payload."""
    if not changes:
        return None

    lines = ['## Anthropic Website Update\n']

    for category, urls in sorted(changes.items()):
        if not urls:
            continue
        lines.append(f'**{category.capitalize()}**:')
        for url in sorted(urls):
            slug = urlparse(url).path.rstrip("/").split("/")[-1]
            lines.append(f'> [{slug}]({url})')
        lines.append('')

    content = "\n".join(lines)

    # Truncate if exceeds 4096 bytes
    content_bytes = content.encode("utf-8")
    if len(content_bytes) > MAX_CONTENT_BYTES:
        # Count total URLs for summary
        total = sum(len(urls) for urls in changes.values())
        suffix = f"\n\n... and more ({total} total updates)"
        suffix_bytes = suffix.encode("utf-8")
        max_body = MAX_CONTENT_BYTES - len(suffix_bytes)

        # Truncate at a line boundary
        truncated = content_bytes[:max_body].decode("utf-8", errors="ignore")
        last_newline = truncated.rfind("\n")
        if last_newline > 0:
            truncated = truncated[:last_newline]
        content = truncated + suffix

    return {
        "msgtype": "markdown",
        "markdown": {
            "content": content,
        },
    }


def send(payload: dict, webhook_url: str) -> None:
    """Send payload to WeChat Work webhook."""
    response = requests.post(webhook_url, json=payload, timeout=10)
    response.raise_for_status()
