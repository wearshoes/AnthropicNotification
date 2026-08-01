"""WeChat Work news-card formatter."""

from src.webhook_http import post_json


FORMATTER_VERSION = 1
MAX_ITEMS_PER_MESSAGE = 8
MAX_ARTICLES = MAX_ITEMS_PER_MESSAGE


def format_message(changes: dict[str, list[dict]]) -> dict | None:
    """Format one bounded chunk as a WeChat Work news payload."""
    if not changes:
        return None
    articles = []
    for category, items in sorted(changes.items()):
        for item in items:
            articles.append({
                "title": item["title"],
                "description": item.get("description") or f"Category: {category.capitalize()}",
                "url": item["url"],
                "picurl": item.get("image") or "",
            })
    if not articles:
        return None
    return {"msgtype": "news", "news": {"articles": articles[:MAX_ARTICLES]}}


def send(payload: dict, webhook_url: str) -> None:
    """Send and require WeChat's business response to report success."""
    post_json(webhook_url, payload)
