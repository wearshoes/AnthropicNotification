"""Reference contract for adding a notification formatter.

Copy this file to ``src/formatters/<platform>.py``, implement both functions,
add ``<PLATFORM>_WEBHOOK`` to GitHub Secrets, and expose that secret in the
workflow's ``Run monitor`` environment.
"""

from src.webhook_http import post_json


FORMATTER_VERSION = 1
MAX_ITEMS_PER_MESSAGE = 10


def format_message(changes: dict[str, list[dict]]) -> dict | None:
    """Format exactly one bounded, enriched chunk into a JSON payload."""
    if not changes:
        return None
    lines = []
    for category, items in sorted(changes.items()):
        if not items:
            continue
        lines.append(f"**{category.capitalize()}**:")
        lines.extend(f"- [{item['title']}]({item['url']})" for item in items)
    if not lines:
        return None
    return {"text": "\n".join(lines)}


def send(payload: dict, webhook_url: str) -> None:
    """Return only after HTTP and platform business status both succeed."""
    post_json(webhook_url, payload)
