# CODEBUDDY.md

This file provides guidance to CodeBuddy Code when working with code in this repository.

## Project Overview

Anthropic website monitor: detect new content via sitemap.xml, store state in GitHub Issues, send webhook notifications. Runs on GitHub Actions every 30 minutes.

## Compound Interest Principle

**This is the core design philosophy of this project.** Every decision should be evaluated through compound interest thinking:

- **Prefer work that creates reusable assets** (skills, templates, conventions) over one-off solutions
- **Stack value incrementally**: each deliverable should be independently useful AND amplify the next
- **End-to-end value streams over horizontal layers**: deliver working slices, not disconnected foundations
- **Extract patterns when they repeat**: if you do something twice, the third time should be a skill or template

When decomposing work, always ask: "Does this make the next task cheaper?"

## Development Workflow

All code changes MUST follow this process:

1. **Explore** (`/opsx:explore`): Think through the problem with compound interest lens
2. **Propose** (`/opsx:propose`): Create OpenSpec change with proposal → specs → design → tasks
3. **Apply** (`/opsx:apply`): Implement with TDD (RED → GREEN → REFACTOR) enforced by hooks
4. **Archive** (`/opsx:archive`): Sync specs and archive the change

### TDD Enforcement

Three layers enforce TDD:
- **Skill**: `/opsx:apply` has TDD instructions built in
- **PreToolUse hook**: Blocks writing `src/**/*.py` if corresponding `tests/test_*.py` doesn't exist
- **PostToolUse hook**: Auto-runs pytest after writing `src/` files, reports results to agent

Files starting with `_` (templates) are exempt from TDD guard.

## Architecture

```
src/
├── main.py              # Orchestrator: sitemap → detector → issues → notifier
├── sitemap.py           # Fetch/parse sitemap.xml, filter by category
├── detector.py          # Compare sitemap URLs vs baseline, find new content
├── issues.py            # GitHub Issues via gh CLI (baseline + update issues)
├── notifier.py          # Convention-based formatter discovery + dispatch
└── formatters/
    ├── _template.py     # Reference template for new formatters
    ├── wechat_work.py   # WeChat Work markdown formatter
    └── dingtalk.py      # DingTalk markdown formatter with HMAC-SHA256 signing
```

## Key Conventions

### Formatter Discovery
- `src/formatters/{name}.py` → auto-discovered by `notifier.py`
- Env var `{NAME}_WEBHOOK` exists → formatter is enabled
- Each formatter exports: `format_message(changes) -> dict | None` and `send(payload, webhook_url) -> None`
- Files starting with `_` are skipped (templates)

### GitHub Issues as State
- One open baseline Issue per category (labels: `baseline,{category}`)
- New content creates update Issues (labels: `{category},update`)
- Labels are auto-created via `gh label create --force`

### Test Structure
- `src/{module}.py` → `tests/test_{module}.py`
- `src/formatters/{name}.py` → `tests/formatters/test_{name}.py`
- Use `pytest` style, mock external dependencies (HTTP, subprocess)

## Commands

```bash
python -m pytest tests/ -v          # Run all tests
python -m src.main --dry-run        # Fetch sitemap only (no detection/notification)
python -m src.main                  # Full run (needs gh CLI + GH_TOKEN)
```

## Adding a Notification Platform

Use `/formatter:add <platform>` skill for guided workflow, or manually:

1. Create `src/formatters/{platform}.py` (reference `_template.py`)
2. Create `tests/formatters/test_{platform}.py` (TDD first)
3. Add `{PLATFORM}_WEBHOOK` env to `.github/workflows/monitor.yml`
4. Add secret to GitHub repo settings

## OpenSpec

Specs live in `openspec/specs/`, archived changes in `openspec/changes/archive/`. Always sync delta specs to main specs before archiving.
