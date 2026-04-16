"""WeChat Work webhook formatter — news article card format."""

import requests

MAX_ARTICLES = 8


def format_message(changes: dict[str, list[dict]]) -> dict | None:
    """Format enriched changes into a WeChat Work news (article card) payload."""
    if not changes:
        return None

    articles = []
    for category, items in sorted(changes.items()):
        for item in items:
            description = item.get("description") or f"Category: {category.capitalize()}"
            article = {
                "title": item["title"],
                "description": description,
                "url": item["url"],
                "picurl": item.get("image") or "",
            }
            articles.append(article)

    if not articles:
        return None

    return {
        "msgtype": "news",
        "news": {
            "articles": articles[:MAX_ARTICLES],
        },
    }


def send(payload: dict, webhook_url: str) -> None:
    """Send payload to WeChat Work webhook."""
    response = requests.post(webhook_url, json=payload, timeout=10)
    response.raise_for_status()
