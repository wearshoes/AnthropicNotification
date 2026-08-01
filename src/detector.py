"""Accept trusted sitemap snapshots into a durable notification outbox."""

from __future__ import annotations

import logging

from src import issues, notifier
from src.outbox import OutboxEvent, make_item, pending_item_ids


logger = logging.getLogger(__name__)


def detect_changes(
    current: set[str],
    known: set[str],
    is_first_run: bool = False,
) -> set[str]:
    """Return URLs in current but not known, except during initial seeding."""
    if is_first_run:
        return set()
    return current - known


def ensure_event_in_baseline(event: OutboxEvent) -> None:
    """Repair the outbox-before-baseline crash window before any delivery."""
    if event.issue_number is None:
        raise ValueError("Cannot repair a baseline from an unpersisted event")
    issue_number, known_urls = issues.get_baseline_issue(event.category)
    if issue_number is None:
        raise issues.GitHubStateError(
            f"[{event.category}] Pending event #{event.issue_number} has no baseline"
        )
    desired = known_urls | {item.url for item in event.items}
    if desired != known_urls:
        issues.update_baseline_issue(issue_number, desired)


def process_category(
    category: str,
    current_urls: set[str],
    pending_events: list[OutboxEvent],
    formatters: list[dict],
) -> list[OutboxEvent]:
    """Persist every split event before advancing a monotonic baseline."""
    issue_number, known_urls = issues.get_baseline_issue(category)
    if issue_number is None:
        issues.create_baseline_issue(category, current_urls)
        logger.info("[%s] First run: created baseline with %s URLs", category, len(current_urls))
        return []

    observed_new = detect_changes(current_urls, known_urls)
    protected_ids = pending_item_ids(pending_events, category=category)
    unowned_urls = {
        url for url in observed_new
        if make_item(category, url).item_id not in protected_ids
    }

    persisted = []
    if unowned_urls:
        planned = notifier.plan_events(category, unowned_urls, formatters)
        for event in planned:
            persisted.append(issues.create_outbox_issue(event))

    monotonic_urls = known_urls | current_urls
    if monotonic_urls != known_urls:
        issues.update_baseline_issue(issue_number, monotonic_urls)

    if persisted:
        logger.info(
            "[%s] Persisted %s new URL(s) across %s event(s)",
            category,
            len(unowned_urls),
            len(persisted),
        )
    return persisted
