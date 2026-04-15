"""Main orchestrator — sitemap → detector → issues → notifier."""

import argparse
import logging
import sys

from src import sitemap, detector, notifier

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def run(dry_run: bool = False) -> dict[str, set[str]] | None:
    """Run the full monitoring pipeline."""
    logger.info("Fetching sitemap...")
    entries = sitemap.fetch_sitemap()
    categorized = sitemap.filter_by_category(entries)

    logger.info(f"Found {sum(len(v) for v in categorized.values())} URLs across {len(categorized)} categories")
    for cat, urls in categorized.items():
        logger.info(f"  {cat}: {len(urls)} URLs")

    if dry_run:
        logger.info("Dry run — skipping detection and notification")
        return categorized

    # Detect changes per category
    all_changes: dict[str, set[str]] = {}
    for category, urls in categorized.items():
        if not urls:
            continue
        new_urls = detector.process_category(category, urls)
        if new_urls:
            all_changes[category] = new_urls

    # Send notifications
    if all_changes:
        total_new = sum(len(v) for v in all_changes.values())
        logger.info(f"Found {total_new} new URL(s) — sending notifications")
        formatters = notifier.discover_formatters()
        notifier.send_notifications(formatters, all_changes)
    else:
        logger.info("No new content detected")

    return None


def main():
    parser = argparse.ArgumentParser(description="Monitor Anthropic website for updates")
    parser.add_argument("--dry-run", action="store_true", help="Fetch and parse sitemap only, no detection or notification")
    args = parser.parse_args()

    try:
        run(dry_run=args.dry_run)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
