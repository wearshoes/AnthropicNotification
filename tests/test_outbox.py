"""Tests for durable notification outbox domain state."""

import pytest


def _planned_chunks(item_ids):
    from src.outbox import make_destination_id

    return [
        {
            "target": "wechat_work",
            "destination_id": make_destination_id("https://hooks.example/wechat_work"),
            "formatter_version": 1,
            "item_ids": item_ids[:1],
            "payload": {"msgtype": "news", "news": {"articles": [{"title": "A"}]}},
        },
        {
            "target": "wechat_work",
            "destination_id": make_destination_id("https://hooks.example/wechat_work"),
            "formatter_version": 1,
            "item_ids": item_ids[1:],
            "payload": {"msgtype": "news", "news": {"articles": [{"title": "B"}]}},
        },
    ]


def test_item_id_is_stable_per_category_and_canonical_url():
    from src.outbox import make_item

    first = make_item("news", "https://www.anthropic.com/news/example")
    second = make_item("news", "https://www.anthropic.com/news/example")
    other_category = make_item("research", "https://www.anthropic.com/news/example")

    assert first.item_id == second.item_id
    assert first.item_id != other_category.item_id
    assert len(first.item_id) == 64


def test_event_round_trip_preserves_fixed_chunks_and_payloads():
    from src.outbox import build_event, make_destination_id, make_item, parse_issue_body, render_issue_body

    items = (
        make_item("news", "https://www.anthropic.com/news/a"),
        make_item("news", "https://www.anthropic.com/news/b"),
    )
    event = build_event(
        "news",
        items,
        _planned_chunks([item.item_id for item in items]),
        created_at="2026-08-02T00:00:00Z",
    )

    restored = parse_issue_body(render_issue_body(event))

    assert restored == event
    assert restored.event_id == event.event_id
    assert restored.chunks[0].payload == event.chunks[0].payload
    assert restored.chunks[0].item_ids == (items[0].item_id,)


def test_receipts_are_monotonic_and_complete_only_after_every_chunk():
    from src.outbox import build_event, make_destination_id, make_item, record_receipt

    items = (
        make_item("news", "https://www.anthropic.com/news/a"),
        make_item("news", "https://www.anthropic.com/news/b"),
    )
    event = build_event(
        "news",
        items,
        _planned_chunks([item.item_id for item in items]),
        created_at="2026-08-02T00:00:00Z",
    )

    first = record_receipt(event, event.chunks[0].chunk_id)
    duplicate = record_receipt(first, event.chunks[0].chunk_id)
    complete = record_receipt(duplicate, event.chunks[1].chunk_id)

    assert first.status == "pending"
    assert duplicate.receipts == first.receipts
    assert complete.status == "delivered"
    assert complete.receipts == frozenset(chunk.chunk_id for chunk in event.chunks)


def test_receipt_rejects_unknown_chunk():
    from src.outbox import build_event, make_destination_id, make_item, record_receipt

    item = make_item("news", "https://www.anthropic.com/news/a")
    event = build_event(
        "news",
        (item,),
        _planned_chunks([item.item_id])[:1],
        created_at="2026-08-02T00:00:00Z",
    )

    with pytest.raises(ValueError, match="Unknown chunk"):
        record_receipt(event, "missing")


def test_render_rejects_issue_body_over_limit():
    from src.outbox import OutboxBodyTooLarge, build_event, make_destination_id, make_item, render_issue_body

    item = make_item("news", "https://www.anthropic.com/news/a")
    chunks = [{
        "target": "wechat_work",
        "destination_id": make_destination_id("https://hooks.example/wechat_work"),
        "formatter_version": 1,
        "item_ids": [item.item_id],
        "payload": {"text": "x" * 1000},
    }]
    event = build_event("news", (item,), chunks, created_at="2026-08-02T00:00:00Z")

    with pytest.raises(OutboxBodyTooLarge):
        render_issue_body(event, max_chars=200)


def test_parse_rejects_body_without_outbox_marker():
    from src.outbox import InvalidOutboxBody, parse_issue_body

    with pytest.raises(InvalidOutboxBody):
        parse_issue_body("ordinary issue body")


def test_pending_item_ids_include_only_pending_events():
    from src.outbox import build_event, make_destination_id, make_item, pending_item_ids, record_receipt

    first = make_item("news", "https://www.anthropic.com/news/a")
    second = make_item("news", "https://www.anthropic.com/news/b")
    pending = build_event(
        "news",
        (first,),
        _planned_chunks([first.item_id])[:1],
        created_at="2026-08-02T00:00:00Z",
    )
    delivered = build_event(
        "news",
        (second,),
        _planned_chunks([second.item_id])[:1],
        created_at="2026-08-02T00:00:00Z",
    )
    delivered = record_receipt(delivered, delivered.chunks[0].chunk_id)

    assert pending_item_ids([pending, delivered], category="news") == {first.item_id}
