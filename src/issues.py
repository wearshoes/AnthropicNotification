"""Manage GitHub Issues as state storage for known URLs via gh CLI."""

import json
import subprocess
from datetime import datetime, timezone
from urllib.parse import urlparse


def _run_gh(args: list[str]) -> subprocess.CompletedProcess:
    """Run a gh CLI command and return the result."""
    return subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
        check=False,
    )


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
