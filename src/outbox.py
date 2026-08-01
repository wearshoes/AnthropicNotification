"""Durable notification outbox domain model."""

from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
import re
from typing import Iterable


SCHEMA_VERSION = 1
DEFAULT_MAX_BODY_CHARS = 60_000
_MARKER_START = "<!-- ANTHROPIC_NOTIFICATION_OUTBOX_V1\n"
_MARKER_END = "\n-->"
_DESTINATION_ID_RE = re.compile(r"url-sha256:[0-9a-f]{64}")


class InvalidOutboxBody(ValueError):
    """Raised when an Issue body does not contain valid outbox state."""


class OutboxBodyTooLarge(ValueError):
    """Raised before an outbox event can exceed the Issue body limit."""


class FrozenDict(dict):
    """JSON-serializable mapping that rejects mutation after construction."""

    def _immutable(self, *args, **kwargs):
        raise TypeError("outbox payloads are immutable")

    __setitem__ = _immutable
    __delitem__ = _immutable
    clear = _immutable
    pop = _immutable
    popitem = _immutable
    setdefault = _immutable
    update = _immutable
    __ior__ = _immutable


@dataclass(frozen=True)
class OutboxItem:
    item_id: str
    url: str


@dataclass(frozen=True)
class OutboxChunk:
    chunk_id: str
    target: str
    destination_id: str
    formatter_version: int
    item_ids: tuple[str, ...]
    payload: FrozenDict


@dataclass(frozen=True)
class OutboxEvent:
    event_id: str
    category: str
    items: tuple[OutboxItem, ...]
    chunks: tuple[OutboxChunk, ...]
    created_at: str
    receipts: frozenset[str] = frozenset()
    status: str = "pending"
    schema_version: int = SCHEMA_VERSION
    issue_number: int | None = None


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def make_item(category: str, canonical_url: str) -> OutboxItem:
    """Create a stable item identity from its category and canonical URL."""
    return OutboxItem(
        item_id=_sha256(f"item/v1\0{category}\0{canonical_url}"),
        url=canonical_url,
    )


def make_destination_id(webhook_url: str) -> str:
    """Create a non-secret identity that detects destination replacement."""
    return "url-sha256:" + _sha256(f"destination/v1\0{webhook_url}")



def _freeze(value):
    if isinstance(value, dict):
        return FrozenDict({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def _snapshot_payload(payload: dict) -> FrozenDict:
    if not isinstance(payload, dict):
        raise ValueError("Outbox payload must be a JSON object")
    try:
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        decoded = json.loads(canonical)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError("Outbox payload must be JSON serializable") from exc
    return _freeze(decoded)


def _event_id(category: str, items: tuple[OutboxItem, ...]) -> str:
    item_ids = "\0".join(sorted(item.item_id for item in items))
    return _sha256(f"event/v1\0{category}\0{item_ids}")


def _chunk_id(
    event_id: str,
    target: str,
    destination_id: str,
    formatter_version: int,
    index: int,
    item_ids: tuple[str, ...],
    payload: dict,
) -> str:
    payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    material = "\0".join((
        "chunk/v1",
        event_id,
        target,
        destination_id,
        str(formatter_version),
        str(index),
        *item_ids,
        payload_json,
    ))
    return _sha256(material)


def _validate_event_structure(event: OutboxEvent) -> None:
    if not event.category or not event.items:
        raise ValueError("Outbox event must contain a category and at least one item")
    item_ids = [item.item_id for item in event.items]
    if len(item_ids) != len(set(item_ids)):
        raise ValueError("Outbox event contains duplicate item IDs")
    for item in event.items:
        if item != make_item(event.category, item.url):
            raise ValueError("Outbox item ID does not match category and URL")
    if not event.chunks:
        raise ValueError("Outbox event must contain at least one chunk")

    known_item_ids = set(item_ids)
    chunk_ids = [chunk.chunk_id for chunk in event.chunks]
    if len(chunk_ids) != len(set(chunk_ids)):
        raise ValueError("Outbox event contains duplicate chunk IDs")
    membership_by_target: dict[str, list[str]] = {}
    for chunk in event.chunks:
        if not chunk.target:
            raise ValueError("Outbox chunk has an invalid target")
        if (
            not isinstance(chunk.destination_id, str)
            or not _DESTINATION_ID_RE.fullmatch(chunk.destination_id)
        ):
            raise ValueError("Outbox chunk has an invalid destination fingerprint")
        if (
            not isinstance(chunk.formatter_version, int)
            or isinstance(chunk.formatter_version, bool)
            or chunk.formatter_version < 1
        ):
            raise ValueError("Outbox chunk has an invalid formatter version")
        if (
            not chunk.item_ids
            or len(chunk.item_ids) != len(set(chunk.item_ids))
            or not set(chunk.item_ids) <= known_item_ids
        ):
            raise ValueError(f"Invalid item membership for target {chunk.target}")
        membership_by_target.setdefault(chunk.target, []).extend(chunk.item_ids)
    for target, membership in membership_by_target.items():
        if len(membership) != len(set(membership)) or set(membership) != known_item_ids:
            raise ValueError(f"Target {target} must cover every item exactly once")


def build_event(
    category: str,
    items: Iterable[OutboxItem],
    planned_chunks: Iterable[dict],
    *,
    created_at: str,
) -> OutboxEvent:
    """Build an event with deeply snapshotted payloads and fixed identities."""
    event_items = tuple(items)
    event_id = _event_id(category, event_items)
    chunks = []
    for index, plan in enumerate(planned_chunks):
        target = str(plan["target"])
        if "destination_id" not in plan:
            raise ValueError(
                f"Outbox chunk for {target} requires a destination fingerprint"
            )
        destination_id = plan["destination_id"]
        formatter_version = int(plan["formatter_version"])
        item_ids = tuple(plan["item_ids"])
        payload = _snapshot_payload(plan["payload"])
        chunks.append(OutboxChunk(
            chunk_id=_chunk_id(
                event_id,
                target,
                destination_id,
                formatter_version,
                index,
                item_ids,
                payload,
            ),
            target=target,
            destination_id=destination_id,
            formatter_version=formatter_version,
            item_ids=item_ids,
            payload=payload,
        ))
    event = OutboxEvent(
        event_id=event_id,
        category=category,
        items=event_items,
        chunks=tuple(chunks),
        created_at=created_at,
    )
    _validate_event_structure(event)
    return event


def _event_data(event: OutboxEvent) -> dict:
    return {
        "schema_version": event.schema_version,
        "event_id": event.event_id,
        "category": event.category,
        "created_at": event.created_at,
        "status": event.status,
        "items": [{"item_id": item.item_id, "url": item.url} for item in event.items],
        "chunks": [{
            "chunk_id": chunk.chunk_id,
            "target": chunk.target,
            "destination_id": chunk.destination_id,
            "formatter_version": chunk.formatter_version,
            "item_ids": list(chunk.item_ids),
            "payload": chunk.payload,
        } for chunk in event.chunks],
        "receipts": sorted(event.receipts),
    }


def render_issue_body(
    event: OutboxEvent,
    *,
    max_chars: int = DEFAULT_MAX_BODY_CHARS,
) -> str:
    """Render readable event details plus a machine-owned JSON state marker."""
    _validate_event_structure(event)
    lines = [
        f"Discovered: {event.created_at}",
        f"Category: {event.category}",
        f"Event-ID: {event.event_id}",
        f"Delivery: {event.status}",
        "",
    ]
    lines.extend(f"- {item.url}" for item in event.items)
    state = json.dumps(_event_data(event), sort_keys=True, separators=(",", ":"))
    body = "\n".join(lines) + "\n\n" + _MARKER_START + state + _MARKER_END
    if len(body) > max_chars:
        raise OutboxBodyTooLarge(
            f"Outbox body is {len(body)} characters; limit is {max_chars}"
        )
    return body


def parse_issue_body(body: str, *, issue_number: int | None = None) -> OutboxEvent:
    """Parse and validate every planning invariant in machine-owned state."""
    match = re.search(
        re.escape(_MARKER_START) + r"(.*?)" + re.escape(_MARKER_END),
        body,
        re.DOTALL,
    )
    if not match:
        raise InvalidOutboxBody("Issue body has no outbox marker")
    try:
        data = json.loads(match.group(1))
        if data["schema_version"] != SCHEMA_VERSION:
            raise InvalidOutboxBody("Unsupported outbox schema version")
        items = tuple(OutboxItem(**item) for item in data["items"])
        chunks = tuple(OutboxChunk(
            chunk_id=chunk["chunk_id"],
            target=chunk["target"],
            destination_id=chunk["destination_id"],
            formatter_version=int(chunk["formatter_version"]),
            item_ids=tuple(chunk["item_ids"]),
            payload=_snapshot_payload(chunk["payload"]),
        ) for chunk in data["chunks"])
        event = OutboxEvent(
            event_id=data["event_id"],
            category=data["category"],
            items=items,
            chunks=chunks,
            created_at=data["created_at"],
            receipts=frozenset(data.get("receipts", [])),
            status=data["status"],
            schema_version=data["schema_version"],
            issue_number=issue_number,
        )
        _validate_event_structure(event)
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        if isinstance(exc, InvalidOutboxBody):
            raise
        raise InvalidOutboxBody(f"Invalid outbox state: {exc}") from exc

    if event.event_id != _event_id(event.category, event.items):
        raise InvalidOutboxBody("Event ID does not match its items")
    chunk_ids = {chunk.chunk_id for chunk in event.chunks}
    if not event.receipts <= chunk_ids:
        raise InvalidOutboxBody("Receipt references an unknown chunk")
    for index, chunk in enumerate(event.chunks):
        expected = _chunk_id(
            event.event_id,
            chunk.target,
            chunk.destination_id,
            chunk.formatter_version,
            index,
            chunk.item_ids,
            chunk.payload,
        )
        if chunk.chunk_id != expected:
            raise InvalidOutboxBody("Chunk ID does not match immutable content")
    expected_status = "delivered" if event.receipts == chunk_ids else "pending"
    if event.status != expected_status:
        raise InvalidOutboxBody("Event status does not match its receipts")
    return event


def record_receipt(event: OutboxEvent, chunk_id: str) -> OutboxEvent:
    """Return a new event with one monotonic chunk receipt recorded."""
    chunk_ids = {chunk.chunk_id for chunk in event.chunks}
    if chunk_id not in chunk_ids:
        raise ValueError(f"Unknown chunk: {chunk_id}")
    receipts = event.receipts | {chunk_id}
    status = "delivered" if receipts == chunk_ids else "pending"
    return replace(event, receipts=frozenset(receipts), status=status)


def pending_item_ids(
    events: Iterable[OutboxEvent],
    *,
    category: str | None = None,
) -> set[str]:
    """Return item IDs currently protected by pending outbox events."""
    return {
        item.item_id
        for event in events
        if event.status == "pending" and (category is None or event.category == category)
        for item in event.items
    }
