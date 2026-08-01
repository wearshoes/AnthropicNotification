"""Plan immutable notification payloads and deliver outbox chunks."""

from __future__ import annotations

from datetime import datetime, timezone
import importlib
import logging
import os
from pathlib import Path
from typing import Callable

from src.enrichment import enrich_urls
from src.outbox import (
    OutboxBodyTooLarge,
    OutboxEvent,
    build_event,
    make_destination_id,
    make_item,
    record_receipt,
    render_issue_body,
)


logger = logging.getLogger(__name__)
FORMATTERS_DIR = Path(__file__).parent / "formatters"


class NoNotificationTargetsError(RuntimeError):
    """Raised when new content exists but no formatter is enabled."""


class FormatterPlanningError(RuntimeError):
    """Raised before state progress when a formatter contract is invalid."""


class DeliveryError(RuntimeError):
    """Aggregate independent chunk failures while retaining saved progress."""

    def __init__(self, event: OutboxEvent, failures: list[str]):
        self.event = event
        self.failures = tuple(failures)
        super().__init__("; ".join(failures))


def discover_formatters() -> list[dict]:
    """Load implemented formatters whose webhook environment variable is set."""
    formatters = []
    for py_file in sorted(FORMATTERS_DIR.glob("*.py")):
        name = py_file.stem
        if name.startswith("_"):
            continue
        if os.environ.get(f"{name.upper()}_ENABLED", "").lower() == "false":
            continue
        webhook_url = os.environ.get(f"{name.upper()}_WEBHOOK")
        if not webhook_url:
            continue
        try:
            module = importlib.import_module(f"src.formatters.{name}")
        except Exception as exc:
            raise FormatterPlanningError(f"Failed to load formatter {name}: {exc}") from exc
        formatters.append({
            "name": name,
            "module": module,
            "webhook_url": webhook_url,
        })
        logger.info("Loaded formatter: %s", name)
    return formatters


def _require_positive_int(module, name: str, target: str) -> int:
    if not hasattr(module, name):
        raise FormatterPlanningError(f"Formatter {target} must define {name}")
    value = getattr(module, name)
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise FormatterPlanningError(
            f"Formatter {target} has invalid {name}: expected a positive integer"
        )
    return value


def _build_event_for_urls(
    category: str,
    ordered_urls: list[str],
    metadata_by_url: dict[str, dict],
    formatters: list[dict],
    created_at: str,
) -> OutboxEvent:
    items = tuple(make_item(category, url) for url in ordered_urls)
    plans = []
    seen_targets = set()
    for formatter in sorted(formatters, key=lambda value: value["name"]):
        target = formatter["name"]
        if target in seen_targets:
            raise FormatterPlanningError(f"Duplicate formatter target: {target}")
        seen_targets.add(target)
        module = formatter["module"]
        version = _require_positive_int(module, "FORMATTER_VERSION", target)
        chunk_size = _require_positive_int(module, "MAX_ITEMS_PER_MESSAGE", target)
        destination_id = make_destination_id(formatter["webhook_url"])
        for offset in range(0, len(items), chunk_size):
            chunk_items = items[offset:offset + chunk_size]
            payload = module.format_message({
                category: [metadata_by_url[item.url] for item in chunk_items]
            })
            if payload is None:
                raise FormatterPlanningError(
                    f"Formatter {target} returned no payload for a non-empty chunk"
                )
            plans.append({
                "target": target,
                "destination_id": destination_id,
                "formatter_version": version,
                "item_ids": [item.item_id for item in chunk_items],
                "payload": payload,
            })
    return build_event(category, items, plans, created_at=created_at)


def plan_events(
    category: str,
    urls: set[str],
    formatters: list[dict],
    *,
    created_at: str | None = None,
) -> list[OutboxEvent]:
    """Enrich once and split the fixed plan into Issue-sized events."""
    if not urls:
        raise ValueError("Cannot plan an empty notification event")
    if not formatters:
        raise NoNotificationTargetsError(
            f"[{category}] New content is blocked because no formatter is enabled"
        )
    ordered_urls = sorted(urls)
    enriched = enrich_urls({category: set(ordered_urls)})
    metadata_by_url = {item["url"]: item for item in enriched.get(category, [])}
    if set(metadata_by_url) != set(ordered_urls):
        raise FormatterPlanningError("Enrichment did not return every planned URL")
    timestamp = created_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def split_group(group: list[str]) -> list[OutboxEvent]:
        event = _build_event_for_urls(
            category, group, metadata_by_url, formatters, timestamp
        )
        try:
            render_issue_body(event)
            return [event]
        except OutboxBodyTooLarge as exc:
            if len(group) == 1:
                raise FormatterPlanningError(
                    f"A single {category} item exceeds the outbox Issue limit"
                ) from exc
            midpoint = len(group) // 2
            return split_group(group[:midpoint]) + split_group(group[midpoint:])

    return split_group(ordered_urls)


def plan_event(
    category: str,
    urls: set[str],
    formatters: list[dict],
    *,
    created_at: str | None = None,
) -> OutboxEvent:
    """Plan a batch that fits one event; production ingestion uses plan_events."""
    events = plan_events(category, urls, formatters, created_at=created_at)
    if len(events) != 1:
        raise FormatterPlanningError("Batch requires multiple outbox events")
    return events[0]


def deliver_event(
    event: OutboxEvent,
    formatters: list[dict],
    *,
    save_event: Callable[[OutboxEvent], OutboxEvent],
) -> OutboxEvent:
    """Deliver every pending chunk and durably save each successful receipt."""
    by_name = {formatter["name"]: formatter for formatter in formatters}
    current = event
    failures = []
    for chunk in event.chunks:
        if chunk.chunk_id in current.receipts:
            continue
        formatter = by_name.get(chunk.target)
        if formatter is None:
            failures.append(f"{chunk.target}/{chunk.chunk_id[:12]}: target credential unavailable")
            continue
        module = formatter["module"]
        try:
            current_version = _require_positive_int(
                module, "FORMATTER_VERSION", chunk.target
            )
        except FormatterPlanningError as exc:
            failures.append(f"{chunk.target}/{chunk.chunk_id[:12]}: {exc}")
            continue
        if current_version != chunk.formatter_version:
            failures.append(
                f"{chunk.target}/{chunk.chunk_id[:12]}: formatter version "
                f"{current_version} cannot send persisted version {chunk.formatter_version}"
            )
            continue
        expected_destination = make_destination_id(formatter["webhook_url"])
        if chunk.destination_id != expected_destination:
            failures.append(
                f"{chunk.target}/{chunk.chunk_id[:12]}: destination identity changed"
            )
            continue
        try:
            module.send(chunk.payload, formatter["webhook_url"])
        except Exception as exc:
            logger.error("Failed chunk %s via %s: %s", chunk.chunk_id, chunk.target, exc)
            failures.append(f"{chunk.target}/{chunk.chunk_id[:12]}: {exc}")
            continue
        current = save_event(record_receipt(current, chunk.chunk_id))
        logger.info("Delivered and receipted chunk %s via %s", chunk.chunk_id, chunk.target)
    if failures:
        raise DeliveryError(current, failures)
    return current
