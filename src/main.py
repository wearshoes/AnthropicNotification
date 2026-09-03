"""Main orchestrator for durable at-least-once notification delivery."""

from __future__ import annotations

import argparse
import logging
import sys

from src import detector, issues, notifier, sitemap
from src.outbox import OutboxEvent


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


class PipelineDeliveryError(RuntimeError):
    """Raised after all independent delivery attempts have completed."""


def _find_conflicting_pending_owners(
    events: list[OutboxEvent],
) -> tuple[set[int | None], list[str]]:
    owners: dict[str, set[int | None]] = {}
    for event in events:
        if event.status != "pending":
            continue
        for item in event.items:
            owners.setdefault(item.item_id, set()).add(event.issue_number)
    conflicts = set()
    failures = []
    for item_id, issue_numbers in owners.items():
        if len(issue_numbers) > 1:
            conflicts.update(issue_numbers)
            rendered = ", ".join(f"#{number}" for number in sorted(issue_numbers))
            failures.append(f"Pending item {item_id} has multiple owners: {rendered}")
    return conflicts, failures


def _deliver_and_finalize(event: OutboxEvent, formatters: list[dict]) -> OutboxEvent:
    delivered = notifier.deliver_event(
        event,
        formatters,
        save_event=issues.save_outbox_event,
    )
    if delivered.status == "delivered":
        # Keep the event discoverable as pending until every finalization step succeeds.
        issues.close_old_update_issues(
            delivered.category,
            exclude_number=delivered.issue_number,
        )
        issues.finalize_outbox_event(delivered)
    return delivered


def _fetch_categorized() -> dict[str, set[str]]:
    logger.info("Fetching sitemap...")
    entries = sitemap.fetch_sitemaps()
    categorized = sitemap.filter_by_category(entries)
    sitemap.validate_snapshot_shape(categorized)
    logger.info(
        "Found %s URLs across %s categories",
        sum(len(value) for value in categorized.values()),
        len(categorized),
    )
    for category, urls in categorized.items():
        logger.info("  %s: %s URLs", category, len(urls))
    return categorized


def run(dry_run: bool = False) -> dict[str, set[str]] | None:
    """Repair and drain pending work, then accept and deliver a new snapshot."""
    if dry_run:
        categorized = _fetch_categorized()
        logger.info("Dry run: skipping detection and notification")
        return categorized

    formatters = notifier.discover_formatters()
    pending_events = issues.list_pending_events()
    conflicting_issues, ownership_failures = _find_conflicting_pending_owners(
        pending_events
    )
    delivery_failures = list(ownership_failures)

    for event in pending_events:
        if event.issue_number in conflicting_issues:
            continue
        detector.ensure_event_in_baseline(event)
        try:
            _deliver_and_finalize(event, formatters)
        except notifier.DeliveryError as exc:
            delivery_failures.append(str(exc))

    categorized = _fetch_categorized()
    known_events = list(pending_events)
    for category, urls in categorized.items():
        new_events = detector.process_category(category, urls, known_events, formatters)
        known_events.extend(new_events)
        for event in new_events:
            try:
                _deliver_and_finalize(event, formatters)
            except notifier.DeliveryError as exc:
                delivery_failures.append(str(exc))

    if delivery_failures:
        raise PipelineDeliveryError(" | ".join(delivery_failures))
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Monitor Anthropic website for updates")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and parse sitemap only, no detection or notification",
    )
    args = parser.parse_args()
    try:
        run(dry_run=args.dry_run)
    except Exception as exc:
        logger.error("Fatal error: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
