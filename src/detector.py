"""Detect new URLs by comparing sitemap content against baseline."""

import logging

from src import issues

logger = logging.getLogger(__name__)


def detect_changes(current: set[str], known: set[str], is_first_run: bool = False) -> set[str]:
    """Return URLs in current but not in known. Returns empty on first run (silent baseline)."""
    if is_first_run:
        return set()
    return current - known


def process_category(category: str, current_urls: set[str]) -> set[str]:
    """Orchestrate detection + issue management for one category. Returns set of new URLs."""
    issue_number, known_urls = issues.get_baseline_issue(category)

    is_first_run = issue_number is None
    new_urls = detect_changes(current_urls, known_urls, is_first_run=is_first_run)

    if is_first_run:
        issues.create_baseline_issue(category, current_urls)
        logger.info(f"[{category}] First run — created baseline with {len(current_urls)} URLs")
        return set()

    if new_urls:
        for url in sorted(new_urls):
            issues.create_update_issue(category, url)
        issues.update_baseline_issue(issue_number, current_urls)
        logger.info(f"[{category}] Found {len(new_urls)} new URL(s)")

    return new_urls
