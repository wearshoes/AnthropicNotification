"""Manage GitHub Issues as fail-closed durable state via the gh CLI."""

from __future__ import annotations

from dataclasses import replace
import json
import logging
import subprocess

from src.outbox import InvalidOutboxBody, OutboxEvent, parse_issue_body, render_issue_body


logger = logging.getLogger(__name__)
GH_TIMEOUT_SECONDS = 30
_ensured_labels: set[str] = set()


class GitHubStateError(RuntimeError):
    """Raised when GitHub state cannot be read, written, or verified."""


class GitHubCommandError(GitHubStateError):
    """Raised when the gh CLI cannot complete a command."""


def _command_name(args: list[str]) -> str:
    return " ".join(args[:2]) if args else "unknown"


def _run_gh(args: list[str]) -> subprocess.CompletedProcess:
    """Run gh with a hard timeout and raise on every failure."""
    try:
        result = subprocess.run(
            ["gh", *args],
            capture_output=True,
            text=True,
            check=False,
            timeout=GH_TIMEOUT_SECONDS,
        )
    except FileNotFoundError as exc:
        raise GitHubCommandError("gh CLI is not installed or not on PATH") from exc
    except subprocess.TimeoutExpired as exc:
        raise GitHubCommandError(
            f"gh {_command_name(args)} timed out after {GH_TIMEOUT_SECONDS}s"
        ) from exc
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "unknown gh error").strip()
        logger.error("gh command failed: gh %s", _command_name(args))
        logger.error("  %s", detail)
        raise GitHubCommandError(f"gh {_command_name(args)} failed: {detail}")
    return result


def _parse_json(output: str, context: str):
    try:
        return json.loads(output)
    except (TypeError, json.JSONDecodeError) as exc:
        raise GitHubStateError(f"Invalid JSON from {context}") from exc


def _parse_paginated_items(output: str, context: str) -> list[dict]:
    pages = _parse_json(output, context)
    if not isinstance(pages, list) or any(
        not isinstance(page, list) for page in pages
    ):
        raise GitHubStateError(f"{context} did not return paginated lists")
    items = []
    for page in pages:
        if any(not isinstance(item, dict) for item in page):
            raise GitHubStateError(f"{context} returned an invalid issue")
        items.extend(page)
    return items


def _extract_issue_number(output: str) -> int:
    try:
        return int(output.strip().rstrip("/").split("/")[-1])
    except (TypeError, ValueError, IndexError) as exc:
        raise GitHubStateError("gh did not return a valid issue number") from exc


def _urls_from_body(body: str) -> set[str]:
    return {
        line.strip()
        for line in body.splitlines()
        if line.strip().startswith("https://")
    }


def _label_names(data: dict) -> set[str]:
    labels = data.get("labels")
    if not isinstance(labels, list):
        raise GitHubStateError("Issue verification returned invalid labels")
    try:
        return {label["name"] for label in labels}
    except (KeyError, TypeError) as exc:
        raise GitHubStateError("Issue verification returned invalid labels") from exc


def _verify_state_and_labels(
    data: dict,
    *,
    state: str,
    required: set[str],
    forbidden: set[str] | None = None,
    context: str,
) -> None:
    actual_state = data.get("state")
    if isinstance(actual_state, str):
        actual_state = actual_state.upper()
    labels = _label_names(data)
    if actual_state != state or not required <= labels or (forbidden or set()) & labels:
        raise GitHubStateError(
            f"{context} verification failed: state={actual_state}, labels={sorted(labels)}"
        )


def _read_issue(issue_number: int) -> dict:
    result = _run_gh([
        "issue", "view", str(issue_number),
        "--json", "number,body,labels,state",
    ])
    data = _parse_json(result.stdout, "gh issue view")
    if not isinstance(data, dict) or int(data.get("number", -1)) != issue_number:
        raise GitHubStateError(f"Issue verification returned the wrong issue for #{issue_number}")
    return data


def _ensure_label(label: str) -> None:
    """Create a label once per process, caching only successful operations."""
    if label in _ensured_labels:
        return
    _run_gh(["label", "create", label, "--force"])
    _ensured_labels.add(label)


def get_baseline_issue(category: str) -> tuple[int | None, set[str]]:
    """Return the newest visible baseline; command failures are never absence."""
    result = _run_gh([
        "issue", "list",
        "--label", f"baseline,{category}",
        "--state", "open",
        "--json", "number,body,labels,state",
        "--limit", "1000",
    ])
    found = _parse_json(result.stdout, "gh issue list baseline")
    if not isinstance(found, list):
        raise GitHubStateError("Baseline query did not return a list")
    if not found:
        return None, set()
    try:
        issue = max(found, key=lambda value: int(value["number"]))
        for candidate in found:
            int(candidate["number"])
            _verify_state_and_labels(
                candidate,
                state="OPEN",
                required={"baseline", category},
                context="Baseline query",
            )
        number = int(issue["number"])
    except (KeyError, TypeError, ValueError) as exc:
        raise GitHubStateError("Baseline query returned an invalid issue") from exc
    if len(found) > 1:
        logger.warning(
            "[%s] Found %s open baselines; using newest #%s",
            category,
            len(found),
            number,
        )
    return number, _urls_from_body(issue.get("body") or "")


def create_baseline_issue(category: str, urls: set[str]) -> int:
    """Create a baseline and verify body, open state, and recovery labels."""
    _ensure_label("baseline")
    _ensure_label(category)
    result = _run_gh([
        "issue", "create",
        "--title", f"[Baseline] {category}",
        "--label", f"baseline,{category}",
        "--body", "\n".join(sorted(urls)),
    ])
    issue_number = _extract_issue_number(result.stdout)
    data = _read_issue(issue_number)
    _verify_state_and_labels(
        data,
        state="OPEN",
        required={"baseline", category},
        context="Baseline creation",
    )
    if _urls_from_body(data.get("body") or "") != urls:
        raise GitHubStateError("Created baseline failed body verification")
    return issue_number


def update_baseline_issue(issue_number: int, urls: set[str]) -> None:
    """Write a monotonic baseline and verify exact body and lifecycle state."""
    before = _read_issue(issue_number)
    _verify_state_and_labels(
        before,
        state="OPEN",
        required={"baseline"},
        context="Baseline precondition",
    )
    current = _urls_from_body(before.get("body") or "")
    if not current <= urls:
        raise GitHubStateError("Baseline update would remove known URLs")
    if current == urls:
        return
    _run_gh([
        "issue", "edit", str(issue_number),
        "--body", "\n".join(sorted(urls)),
    ])
    after = _read_issue(issue_number)
    _verify_state_and_labels(
        after,
        state="OPEN",
        required={"baseline"},
        context="Baseline update",
    )
    if _urls_from_body(after.get("body") or "") != urls:
        raise GitHubStateError("Baseline update failed body verification")


def get_outbox_event(issue_number: int) -> OutboxEvent:
    """Read and validate one open, recoverable outbox Issue."""
    data = _read_issue(issue_number)
    try:
        event = parse_issue_body(data.get("body") or "", issue_number=issue_number)
    except InvalidOutboxBody as exc:
        raise GitHubStateError(f"Invalid outbox Issue #{issue_number}: {exc}") from exc
    _verify_state_and_labels(
        data,
        state="OPEN",
        required={event.category, "update", "notification-pending"},
        context=f"Outbox #{issue_number}",
    )
    return event


def create_outbox_issue(event: OutboxEvent) -> OutboxEvent:
    """Persist an outbox event, then verify body, labels, and open state."""
    if event.issue_number is not None:
        raise ValueError("Outbox event is already persisted")
    _ensure_label(event.category)
    _ensure_label("update")
    _ensure_label("notification-pending")
    title = (
        f"[{event.category.capitalize()}] {len(event.items)} pending update(s) "
        f"[{event.event_id[:12]}]"
    )
    result = _run_gh([
        "issue", "create",
        "--title", title,
        "--label", f"{event.category},update,notification-pending",
        "--body", render_issue_body(event),
    ])
    issue_number = _extract_issue_number(result.stdout)
    verified = get_outbox_event(issue_number)
    if replace(verified, issue_number=None) != event:
        raise GitHubStateError("Persisted outbox event failed exact verification")
    return verified


def list_pending_events() -> list[OutboxEvent]:
    """Discover machine outboxes even if their pending label was removed."""
    result = _run_gh([
        "api", "--method", "GET", "--paginate", "--slurp",
        "repos/{owner}/{repo}/issues?state=all&labels=update&per_page=100",
    ])
    found = _parse_paginated_items(result.stdout, "gh api outbox query")
    events = []
    for issue in found:
        if "pull_request" in issue:
            pull_request = issue["pull_request"]
            if not isinstance(pull_request, dict) or not isinstance(
                pull_request.get("url"), str
            ) or not pull_request["url"]:
                raise GitHubStateError("Outbox query returned invalid pull_request marker")
            continue
        body = issue.get("body") or ""
        if "ANTHROPIC_NOTIFICATION_OUTBOX_V1" not in body:
            continue
        try:
            number = int(issue["number"])
            event = parse_issue_body(body, issue_number=number)
            labels = _label_names(issue)
            raw_state = issue.get("state")
            state = raw_state.upper() if isinstance(raw_state, str) else raw_state

            if (
                event.status == "delivered"
                and "notification-delivered" in labels
                and "notification-pending" not in labels
            ):
                if (
                    state not in {"OPEN", "CLOSED"}
                    or not {event.category, "update"} <= labels
                ):
                    raise GitHubStateError(
                        f"Delivered Issue #{number} has invalid lifecycle state"
                    )
                continue

            if state != "OPEN":
                raise GitHubStateError(f"Pending Issue #{number} is closed")
            if "notification-pending" not in labels:
                _ensure_label("notification-pending")
                _run_gh([
                    "issue", "edit", str(number),
                    "--add-label", "notification-pending",
                ])
                issue = _read_issue(number)
                repaired = parse_issue_body(
                    issue.get("body") or "", issue_number=number
                )
                if repaired != event:
                    raise GitHubStateError(
                        f"Pending label repair changed outbox Issue #{number}"
                    )
                event = repaired
            _verify_state_and_labels(
                issue,
                state="OPEN",
                required={event.category, "update", "notification-pending"},
                context=f"Pending Issue #{number}",
            )
            events.append(event)
        except GitHubStateError:
            raise
        except (InvalidOutboxBody, KeyError, TypeError, ValueError) as exc:
            raise GitHubStateError("Outbox Issue contains invalid machine state") from exc
    return sorted(events, key=lambda event: event.issue_number or 0)


def save_outbox_event(event: OutboxEvent) -> OutboxEvent:
    """Persist receipt progress and verify the exact recoverable event."""
    if event.issue_number is None:
        raise ValueError("Cannot save an unpersisted outbox event")
    _run_gh([
        "issue", "edit", str(event.issue_number),
        "--body", render_issue_body(event),
    ])
    verified = get_outbox_event(event.issue_number)
    if verified != event:
        raise GitHubStateError("Outbox receipt verification failed")
    return verified


def finalize_outbox_event(event: OutboxEvent) -> None:
    """Move a fully receipted event to delivered and verify the transition."""
    if event.issue_number is None:
        raise ValueError("Cannot finalize an unpersisted outbox event")
    if event.status != "delivered":
        raise ValueError("Outbox event is not fully delivered")
    _ensure_label("notification-delivered")
    _run_gh([
        "issue", "edit", str(event.issue_number),
        "--add-label", "notification-delivered",
        "--remove-label", "notification-pending",
    ])
    data = _read_issue(event.issue_number)
    _verify_state_and_labels(
        data,
        state="OPEN",
        required={event.category, "update", "notification-delivered"},
        forbidden={"notification-pending"},
        context="Outbox finalization",
    )


def close_old_update_issues(category: str, exclude_number: int | None = None) -> None:
    """Close older display Issues without ever closing pending outbox work."""
    if exclude_number is None:
        raise ValueError("exclude_number is required when closing update Issues")
    result = _run_gh([
        "issue", "list",
        "--label", f"{category},update",
        "--state", "open",
        "--json", "number,labels",
        "--limit", "1000",
    ])
    found = _parse_json(result.stdout, "gh issue list old updates")
    if not isinstance(found, list):
        raise GitHubStateError("Old update query did not return a list")
    for issue in found:
        number = int(issue["number"])
        labels = _label_names(issue)
        if number == exclude_number or "notification-pending" in labels:
            continue
        _run_gh(["issue", "close", str(number)])
        closed = _read_issue(number)
        if closed.get("state") != "CLOSED":
            raise GitHubStateError(f"Closing old update Issue #{number} was not verified")
        logger.info("Closed old update issue #%s for %s", number, category)
