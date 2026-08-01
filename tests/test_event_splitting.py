"""Tests for splitting oversized batches into independently durable events."""

from unittest.mock import patch


@patch("src.notifier.enrich_urls")
def test_large_batch_splits_into_issue_sized_events_without_loss(mock_enrich):
    from src.formatters import wechat_work
    from src.notifier import plan_events
    from src.outbox import render_issue_body

    urls = {f"https://www.anthropic.com/news/article-{index:03d}" for index in range(250)}
    mock_enrich.return_value = {
        "news": [{
            "url": url,
            "title": f"Title {url[-3:]}",
            "description": "d" * 300,
            "image": "https://www.anthropic.com/images/example.jpg",
        } for url in sorted(urls)]
    }
    formatter = {
        "name": "wechat_work",
        "module": wechat_work,
        "webhook_url": "https://hooks.example/wechat",
    }

    events = plan_events(
        "news", urls, [formatter], created_at="2026-08-02T00:00:00Z"
    )

    assert len(events) > 1
    assert {item.url for event in events for item in event.items} == urls
    assert sum(len(event.items) for event in events) == len(urls)
    assert all(len(render_issue_body(event)) <= 60_000 for event in events)
