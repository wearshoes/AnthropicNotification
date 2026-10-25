"""Tests for the durable main orchestrator."""

from dataclasses import replace
import sys
from unittest.mock import call, patch

import pytest


def _event():
    from src.outbox import build_event, make_destination_id, make_item

    item = make_item("news", "https://www.anthropic.com/news/a")
    return replace(build_event(
        "news",
        (item,),
        [{
            "target": "wechat_work",
            "destination_id": make_destination_id("https://hooks.example/wechat_work"),
            "formatter_version": 1,
            "item_ids": [item.item_id],
            "payload": {"msgtype": "news"},
        }],
        created_at="2026-08-02T00:00:00Z",
    ), issue_number=101)


class TestFinalization:
    @patch("src.main.notifier")
    @patch("src.main.issues")
    def test_cleanup_finishes_before_pending_label_is_removed(
        self, mock_issues, mock_notifier
    ):
        from src.main import _deliver_and_finalize
        from src.outbox import record_receipt

        event = _event()
        delivered = record_receipt(event, event.chunks[0].chunk_id)
        mock_notifier.deliver_event.return_value = delivered

        _deliver_and_finalize(event, [{"name": "wechat_work"}])

        assert mock_issues.method_calls == [
            call.close_old_update_issues("news", exclude_number=101),
            call.finalize_outbox_event(delivered),
        ]

    @patch("src.main.notifier")
    @patch("src.main.issues")
    def test_cleanup_failure_leaves_event_pending(self, mock_issues, mock_notifier):
        from src.main import _deliver_and_finalize
        from src.outbox import record_receipt

        event = _event()
        delivered = record_receipt(event, event.chunks[0].chunk_id)
        mock_notifier.deliver_event.return_value = delivered
        mock_issues.close_old_update_issues.side_effect = RuntimeError("cleanup failed")

        with pytest.raises(RuntimeError, match="cleanup failed"):
            _deliver_and_finalize(event, [{"name": "wechat_work"}])

        mock_issues.finalize_outbox_event.assert_not_called()


class TestRun:
    @patch("src.main.notifier")
    @patch("src.main.detector")
    @patch("src.main.issues")
    @patch("src.main.sitemap")
    def test_full_flow_delivers_each_new_event(
        self, mock_sitemap, mock_issues, mock_detector, mock_notifier
    ):
        from src.main import run
        from src.outbox import record_receipt

        event = _event()
        delivered = record_receipt(event, event.chunks[0].chunk_id)
        mock_issues.list_pending_events.return_value = []
        mock_sitemap.fetch_sitemaps.return_value = [{"loc": event.items[0].url}]
        mock_sitemap.fetch_engineering_urls.return_value = set()
        mock_sitemap.filter_by_category.return_value = {
            "news": {event.items[0].url}, "research": set(),
            "engineering": set(), "learn": set(),
        }
        mock_detector.process_category.side_effect = [[event], [], [], []]
        mock_notifier.discover_formatters.return_value = [{"name": "wechat_work"}]
        mock_notifier.deliver_event.return_value = delivered

        run()

        mock_sitemap.filter_by_category.assert_called_once_with(
            [{"loc": event.items[0].url}], set()
        )
        assert mock_detector.process_category.call_count == 4
        mock_notifier.deliver_event.assert_called_once()
        mock_issues.finalize_outbox_event.assert_called_once_with(delivered)

    @patch("src.main.notifier")
    @patch("src.main.detector")
    @patch("src.main.issues")
    @patch("src.main.sitemap")
    def test_no_changes_attempts_all_categories(
        self, mock_sitemap, mock_issues, mock_detector, mock_notifier
    ):
        from src.main import run

        mock_issues.list_pending_events.return_value = []
        mock_sitemap.fetch_sitemaps.return_value = []
        mock_sitemap.filter_by_category.return_value = {
            "news": set(), "research": set(), "engineering": set(), "learn": set()
        }
        mock_detector.process_category.return_value = []
        mock_notifier.discover_formatters.return_value = []
        run()
        assert mock_detector.process_category.call_count == 4

    @patch("src.main.notifier")
    @patch("src.main.issues")
    @patch("src.main.sitemap")
    def test_sitemap_error_raises_after_pending_query(
        self, mock_sitemap, mock_issues, mock_notifier
    ):
        from src.main import run

        mock_issues.list_pending_events.return_value = []
        mock_notifier.discover_formatters.return_value = []
        mock_sitemap.fetch_sitemaps.side_effect = RuntimeError("network error")
        with pytest.raises(RuntimeError, match="network error"):
            run()


class TestDryRun:
    @patch("src.main.issues")
    @patch("src.main.notifier")
    @patch("src.main.detector")
    @patch("src.main.sitemap")
    def test_dry_run_has_no_state_calls(
        self, mock_sitemap, mock_detector, mock_notifier, mock_issues
    ):
        from src.main import run

        categorized = {"news": {"https://www.anthropic.com/news/a"}}
        mock_sitemap.fetch_sitemaps.return_value = []
        mock_sitemap.filter_by_category.return_value = categorized
        assert run(dry_run=True) == categorized
        mock_issues.list_pending_events.assert_not_called()
        mock_detector.process_category.assert_not_called()


class TestFailureReporting:
    def test_incomplete_snapshot_has_chinese_reason_and_safe_detail(self):
        from src.main import _build_failure_report
        from src.sitemap import IncompleteSitemapError

        report = _build_failure_report(IncompleteSitemapError(
            "Sitemap snapshot is incomplete: total=497, empty=engineering"
        ))

        assert report.reason == "内容源快照不完整，安全检查已阻止本轮继续执行。"
        assert report.suggestion == "检查上游 Sitemap、Engineering 页面结构和分类规则。"
        assert report.detail == (
            "Sitemap snapshot is incomplete: total=497, empty=engineering"
        )

    def test_known_failure_classes_have_actionable_chinese_reason(self):
        import requests

        from src import notifier
        from src.main import PipelineDeliveryError, _build_failure_report
        from src.sitemap import UntrustedUrlError

        cases = [
            (
                UntrustedUrlError("URL is outside the trusted content origins"),
                "内容源地址或重定向离开了允许的 Anthropic 域名。",
            ),
            (
                requests.Timeout("TOPSECRET"),
                "访问 Anthropic 或 Claude Academy 内容源失败，本轮快照未完成。",
            ),
            (
                notifier.NoNotificationTargetsError(
                    "[news] New content is blocked because no formatter is enabled"
                ),
                "检测到新增内容，但没有可用的通知通道，基线未继续推进。",
            ),
            (
                notifier.FormatterPlanningError("TOPSECRET"),
                "通知消息规划失败，为避免漏发，本轮未推进相应状态。",
            ),
            (
                PipelineDeliveryError("TOPSECRET"),
                "通知未全部发送或回执，本轮任务未完成。",
            ),
        ]

        for error, expected_reason in cases:
            report = _build_failure_report(error)
            assert report.reason == expected_reason
            assert report.suggestion
            if "TOPSECRET" in str(error):
                assert "TOPSECRET" not in " ".join(
                    part
                    for part in (report.reason, report.suggestion, report.detail)
                    if part
                )

    def test_unknown_error_omits_arbitrary_message(self):
        from src.main import _build_failure_report

        report = _build_failure_report(RuntimeError(
            "failed for https://hooks.example/send?key=TOPSECRET"
        ))

        assert report.reason == "监控任务发生未分类异常，本轮未完成。"
        assert report.detail == "异常类型：RuntimeError"
        rendered = " ".join((report.reason, report.suggestion, report.detail))
        assert "TOPSECRET" not in rendered
        assert "https://" not in rendered

    def test_github_state_error_omits_cli_output(self):
        from src.issues import GitHubStateError
        from src.main import _build_failure_report

        report = _build_failure_report(GitHubStateError(
            "gh api failed: authorization Bearer TOPSECRET"
        ))

        assert report.reason == "GitHub Issue 状态读取、写入或回读校验失败。"
        assert report.detail == "异常类型：GitHubStateError"
        assert "TOPSECRET" not in " ".join(
            (report.reason, report.suggestion, report.detail)
        )

    def test_github_actions_annotation_and_summary_are_chinese_and_escaped(
        self, monkeypatch, tmp_path, capsys
    ):
        from src.main import FailureReport, _emit_failure_report

        summary = tmp_path / "step-summary.md"
        monkeypatch.setenv("GITHUB_ACTIONS", "true")
        monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
        report = FailureReport(
            reason="第一行%完成\n第二行",
            suggestion="检查配置",
            detail="异常类型：ExampleError",
        )

        _emit_failure_report(report)

        annotation = capsys.readouterr().err
        assert annotation.startswith("::error title=监控任务未完成::")
        assert "%25" in annotation
        assert "%0A" in annotation
        markdown = summary.read_text(encoding="utf-8")
        assert "## 监控任务未完成" in markdown
        assert "- **原因**：第一行%完成\n第二行" in markdown
        assert "- **处理建议**：检查配置" in markdown
        assert "- **技术信息**：异常类型：ExampleError" in markdown

    def test_unwritable_summary_does_not_replace_original_failure(
        self, monkeypatch, tmp_path, caplog
    ):
        from src.main import FailureReport, _emit_failure_report

        monkeypatch.setenv("GITHUB_ACTIONS", "true")
        monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(tmp_path))
        report = FailureReport("失败", "检查", "异常类型：ExampleError")

        _emit_failure_report(report)

        assert "无法写入 GitHub Actions 运行摘要" in caplog.text

    @patch("src.main._emit_failure_report")
    @patch("src.main.run")
    def test_main_reports_failure_and_keeps_nonzero_exit(
        self, mock_run, mock_emit, monkeypatch
    ):
        from src.main import main
        from src.sitemap import IncompleteSitemapError

        mock_run.side_effect = IncompleteSitemapError(
            "Sitemap snapshot is incomplete: total=497, empty=engineering"
        )
        monkeypatch.setattr(sys, "argv", ["monitor"])

        with pytest.raises(SystemExit) as raised:
            main()

        assert raised.value.code == 1
        report = mock_emit.call_args.args[0]
        assert "内容源快照不完整" in report.reason
