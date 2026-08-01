"""Adversarial validation and immutability tests for outbox state."""

import json

import pytest


def _rewrite_state(body, mutate):
    start = "<!-- ANTHROPIC_NOTIFICATION_OUTBOX_V1\n"
    prefix, marked = body.split(start, 1)
    raw, suffix = marked.split("\n-->", 1)
    state = json.loads(raw)
    mutate(state)
    return prefix + start + json.dumps(state, sort_keys=True, separators=(",", ":")) + "\n-->" + suffix


def _two_item_event():
    from src.outbox import build_event, make_destination_id, make_item

    items = (
        make_item("news", "https://www.anthropic.com/news/a"),
        make_item("news", "https://www.anthropic.com/news/b"),
    )
    return build_event(
        "news",
        items,
        [{
            "target": "wechat_work",
            "destination_id": make_destination_id("https://hooks.example/wechat_work"),
            "formatter_version": 1,
            "item_ids": [item.item_id for item in items],
            "payload": {"news": {"articles": [{"title": "A"}, {"title": "B"}]}},
        }],
        created_at="2026-08-02T00:00:00Z",
    )


def test_build_event_requires_url_destination_fingerprint():
    from src.outbox import build_event, make_item

    item = make_item("news", "https://www.anthropic.com/news/a")
    common = {
        "target": "wechat_work",
        "formatter_version": 1,
        "item_ids": [item.item_id],
        "payload": {"msgtype": "news"},
    }
    with pytest.raises(ValueError, match="destination"):
        build_event("news", (item,), [common], created_at="2026-08-02T00:00:00Z")
    with pytest.raises(ValueError, match="destination"):
        build_event(
            "news",
            (item,),
            [{**common, "destination_id": "target-sha256:" + "0" * 64}],
            created_at="2026-08-02T00:00:00Z",
        )


def test_parse_rejects_event_without_chunks_even_if_status_says_delivered():
    from src.outbox import InvalidOutboxBody, parse_issue_body, render_issue_body

    body = _rewrite_state(
        render_issue_body(_two_item_event()),
        lambda state: state.update(chunks=[], receipts=[], status="delivered"),
    )
    with pytest.raises(InvalidOutboxBody, match="chunk"):
        parse_issue_body(body)


def test_parse_rejects_target_that_does_not_cover_every_item():
    from src.outbox import InvalidOutboxBody, parse_issue_body, render_issue_body

    event = _two_item_event()
    body = _rewrite_state(
        render_issue_body(event),
        lambda state: state["items"].append({
            "item_id": "0" * 64,
            "url": "https://www.anthropic.com/news/c",
        }),
    )
    with pytest.raises(InvalidOutboxBody):
        parse_issue_body(body)


def test_build_event_deeply_snapshots_payload_from_caller_mutation():
    from src.outbox import build_event, make_destination_id, make_item

    item = make_item("news", "https://www.anthropic.com/news/a")
    payload = {"nested": {"values": ["original"]}}
    event = build_event(
        "news",
        (item,),
        [{
            "target": "wechat_work",
            "destination_id": make_destination_id("https://hooks.example/wechat_work"),
            "formatter_version": 1,
            "item_ids": [item.item_id],
            "payload": payload,
        }],
        created_at="2026-08-02T00:00:00Z",
    )
    payload["nested"]["values"][0] = "mutated"

    assert event.chunks[0].payload["nested"]["values"][0] == "original"
    with pytest.raises(TypeError):
        event.chunks[0].payload["new"] = "blocked"
