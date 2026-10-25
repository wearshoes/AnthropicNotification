"""Main orchestrator for durable at-least-once notification delivery."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import logging
import os
import sys

import requests

from src import detector, issues, notifier, sitemap
from src.outbox import OutboxEvent


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


class PipelineDeliveryError(RuntimeError):
    """Raised after all independent delivery attempts have completed."""


@dataclass(frozen=True)
class FailureReport:
    """Credential-safe explanation for an operator-facing pipeline failure."""

    reason: str
    suggestion: str
    detail: str | None = None


def _exception_type_detail(exc: Exception) -> str:
    return f"异常类型：{type(exc).__name__}"


def _build_failure_report(exc: Exception) -> FailureReport:
    """Map expected failures to Chinese guidance without exposing arbitrary text."""
    if isinstance(exc, sitemap.IncompleteSitemapError):
        return FailureReport(
            reason="内容源快照不完整，安全检查已阻止本轮继续执行。",
            suggestion="检查上游 Sitemap、Engineering 页面结构和分类规则。",
            detail=str(exc),
        )
    if isinstance(exc, sitemap.UntrustedUrlError):
        return FailureReport(
            reason="内容源地址或重定向离开了允许的 Anthropic 域名。",
            suggestion="检查上游 Sitemap 和 Engineering 页面中的链接或重定向。",
            detail=str(exc),
        )
    if isinstance(exc, requests.RequestException):
        return FailureReport(
            reason="访问 Anthropic 或 Claude Academy 内容源失败，本轮快照未完成。",
            suggestion="检查上游网站可用性、网络连接和重定向状态。",
            detail=_exception_type_detail(exc),
        )
    if isinstance(exc, issues.GitHubStateError):
        return FailureReport(
            reason="GitHub Issue 状态读取、写入或回读校验失败。",
            suggestion=(
                "检查 Actions 的 issues: write 权限、GITHUB_TOKEN 和 GitHub 服务状态。"
            ),
            detail=_exception_type_detail(exc),
        )
    if isinstance(exc, notifier.NoNotificationTargetsError):
        return FailureReport(
            reason="检测到新增内容，但没有可用的通知通道，基线未继续推进。",
            suggestion="检查 WECHAT_WORK_WEBHOOK 或 DINGTALK_WEBHOOK 仓库 Secret。",
            detail=str(exc),
        )
    if isinstance(exc, notifier.FormatterPlanningError):
        return FailureReport(
            reason="通知消息规划失败，为避免漏发，本轮未推进相应状态。",
            suggestion="检查已启用通知格式器的版本、分块配置和消息格式。",
            detail=_exception_type_detail(exc),
        )
    if isinstance(exc, (PipelineDeliveryError, notifier.DeliveryError)):
        return FailureReport(
            reason="通知未全部发送或回执，本轮任务未完成。",
            suggestion=(
                "检查企业微信或钉钉 Webhook、平台返回码和 notification-pending "
                "Issue；下次运行会重试未回执消息。"
            ),
            detail=_exception_type_detail(exc),
        )
    return FailureReport(
        reason="监控任务发生未分类异常，本轮未完成。",
        suggestion="查看本步骤上方日志和异常类型；如重复出现，再补充专门诊断。",
        detail=_exception_type_detail(exc),
    )


def _escape_workflow_command_data(value: str) -> str:
    return value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def _render_failure_markdown(report: FailureReport) -> str:
    lines = [
        "## 监控任务未完成",
        "",
        f"- **原因**：{report.reason}",
        f"- **处理建议**：{report.suggestion}",
    ]
    if report.detail:
        lines.append(f"- **技术信息**：{report.detail}")
    return "\n".join(lines) + "\n"


def _emit_failure_report(report: FailureReport) -> None:
    """Log the report and add Actions UI output without masking the failure."""
    logger.error("监控任务未完成：%s", report.reason)
    logger.error("处理建议：%s", report.suggestion)
    if report.detail:
        logger.error("技术信息：%s", report.detail)

    if os.environ.get("GITHUB_ACTIONS", "").lower() != "true":
        return

    annotation_lines = [
        f"原因：{report.reason}",
        f"处理建议：{report.suggestion}",
    ]
    if report.detail:
        annotation_lines.append(f"技术信息：{report.detail}")
    annotation = _escape_workflow_command_data("\n".join(annotation_lines))
    print(f"::error title=监控任务未完成::{annotation}", file=sys.stderr, flush=True)

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return
    try:
        with open(summary_path, "a", encoding="utf-8", newline="\n") as summary:
            summary.write(_render_failure_markdown(report))
    except OSError as summary_error:
        logger.warning(
            "无法写入 GitHub Actions 运行摘要：%s",
            type(summary_error).__name__,
        )


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
    logger.info("Fetching content sources...")
    entries = sitemap.fetch_sitemaps()
    engineering_urls = sitemap.fetch_engineering_urls()
    categorized = sitemap.filter_by_category(entries, engineering_urls)
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
        _emit_failure_report(_build_failure_report(exc))
        sys.exit(1)


if __name__ == "__main__":
    main()
