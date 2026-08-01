"""Static safety checks for the GitHub Actions workflow."""

from pathlib import Path
import re


WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "monitor.yml"


def test_monitor_workflow_has_single_writer_and_timeout():
    content = WORKFLOW.read_text(encoding="utf-8")

    assert "concurrency:" in content
    assert "group: anthropic-notification-monitor" in content
    assert "cancel-in-progress: false" in content
    assert "timeout-minutes:" in content


def test_monitor_workflow_runs_tests_before_monitor():
    content = WORKFLOW.read_text(encoding="utf-8")

    test_position = content.index("python -m pytest")
    monitor_position = content.index("python -m src.main")
    assert test_position < monitor_position


def test_third_party_actions_are_pinned_to_commits():
    content = WORKFLOW.read_text(encoding="utf-8")
    action_refs = re.findall(r"uses:\s+([^\s]+)", content)

    assert action_refs
    for action_ref in action_refs:
        _, separator, revision = action_ref.partition("@")
        assert separator == "@"
        assert re.fullmatch(r"[0-9a-f]{40}", revision)
