"""Manage GitHub Issues as state storage for known URLs via gh CLI."""

import json
import logging
import subprocess
from datetime import datetime, timezone
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

_ensured_labels: set[str] = set()


def _ensure_label(label: str) -> None:
    """Create a label if it doesn't exist yet (idempotent, cached per run)."""
    if label in _ensured_labels:
        return
    _run_gh(["label", "create", label, "--force"])
    _ensured_labels.add(label)


def _run_gh(args: list[str]) -> subprocess.CompletedProcess:
    """Run a gh CLI command and return the result."""
    result = subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        logger.error(f"gh command failed: gh {' '.join(args)}")
        logger.error(f"  stdout: {result.stdout}")
        logger.error(f"  stderr: {result.stderr}")
    return result


def get_baseline_issue(category: str) -> tuple[int | None, set[str]]:
    """Find the open baseline Issue for a category. Returns (issue_number, set_of_urls)."""
    result = _run_gh([
        "issue", "list",
        "--label", f"baseline,{category}",
        "--state", "open",
        "--json", "number,body",
        "--limit", "1",
    ])

    if result.returncode != 0:
        return None, set()

    issues = json.loads(result.stdout)
    if not issues:
        return None, set()

    issue = issues[0]
    body = issue.get("body", "")
    urls = {line.strip() for line in body.splitlines() if line.strip()}
    return issue["number"], urls


def create_baseline_issue(category: str, urls: set[str]) -> None:
    """Create a new baseline Issue for a category."""
    _ensure_label("baseline")
    _ensure_label(category)
    body = "\n".join(sorted(urls))
    _run_gh([
        "issue", "create",
        "--title", f"[Baseline] {category}",
        "--label", f"baseline,{category}",
        "--body", body,
    ])


def update_baseline_issue(issue_number: int, urls: set[str]) -> None:
    """Update the baseline Issue body with the full set of URLs."""
    body = "\n".join(sorted(urls))
    _run_gh([
        "issue", "edit",
        str(issue_number),
        "--body", body,
    ])


def create_update_issue(category: str, url: str) -> None:
    """Create an Issue for a newly discovered URL."""
    _ensure_label(category)
    _ensure_label("update")
    slug = urlparse(url).path.rstrip("/").split("/")[-1]
    title = f"[{category.capitalize()}] {slug}"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    body = f"URL: {url}\nDiscovered: {now}\nCategory: {category}"

    _run_gh([
        "issue", "create",
        "--title", title,
        "--label", f"{category},update",
        "--body", body,
    ])
