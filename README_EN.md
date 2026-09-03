# Anthropic Notification

English | [中文](README.md)

Monitor new content published on [Anthropic](https://www.anthropic.com) and [Claude Academy](https://academy.claude.com), then deliver webhook notifications through WeChat Work or DingTalk.

## Features

- Two-sitemap monitoring for news, research, engineering, and learn pages
- GitHub Issues as a durable baseline and notification outbox
- At-least-once delivery with per-message receipts and automatic retry
- Complete message chunking: WeChat Work sends at most 8 articles per message without dropping the remainder
- Automatic outbox-event splitting when a batch would exceed the GitHub Issue body limit
- Page title, description, and cover-image enrichment
- Fail-closed GitHub and webhook operations
- Serialized, time-bounded GitHub Actions runs
- Silent baseline creation on first run

## Reliability Model

New URLs are processed in this order:

1. Validate and canonicalize the sitemap snapshot.
2. Enrich the new pages and persist fixed targets, destination fingerprints, and payload chunks in one or more size-bounded outbox Issues.
3. Re-read the Issue to verify persistence.
4. Extend the baseline using `known URLs ∪ current URLs`.
5. Send each pending chunk and persist its receipt immediately.
6. Mark the Issue delivered after every target chunk has a receipt.

Webhook APIs do not provide an idempotency key. If a process stops after a webhook accepts a message but before its receipt is saved, that chunk can be sent again. The guarantee is therefore durable **at-least-once delivery**, not exactly-once delivery. A GitHub API failure, missing target credential, formatter-version mismatch, HTTP failure, or non-zero platform `errcode` keeps work pending and fails the run.

The workflow requests a run every 30 minutes, but GitHub Actions scheduled execution is best-effort and can be delayed or skipped by GitHub. Use `workflow_dispatch` when an immediate check is required.

## Monitored Pages

| Category | Source and URL Pattern | Content |
|----------|------------------------|---------|
| news | `www.anthropic.com/news/*` | Product launches and company announcements |
| research | `www.anthropic.com/research/*` | AI safety papers and technical reports |
| engineering | `www.anthropic.com/engineering/*` | Engineering posts |
| learn | `academy.claude.com/collections/*` | Claude Academy learning collections |

Only category-routed canonical HTTPS URLs on the exact `www.anthropic.com` or `academy.claude.com` host are accepted. Academy course lessons, tutorials, and index pages do not enter the learn category. A snapshot is rejected unless all four categories are non-empty and their combined content count is at least 300. Existing baselines never shrink.

## Quick Start

1. Fork this repository.
2. In **Settings → Secrets and variables → Actions**, configure at least one implemented webhook:

| Secret | Description | Required |
|--------|-------------|----------|
| `WECHAT_WORK_WEBHOOK` | WeChat Work bot webhook URL | At least one target |
| `DINGTALK_WEBHOOK` | DingTalk custom robot webhook URL | At least one target |
| `DINGTALK_SECRET` | Optional DingTalk signing secret | Optional |

3. Enable GitHub Actions in the fork.
4. Run **Monitor Anthropic Website** manually once.

The first successful run creates one baseline Issue for each of the four categories and sends no notification. Later runs create machine-owned update Issues for newly accepted content. If no formatter is enabled when new content appears, the run fails and the baseline does not advance.

## Supported Platforms

| Platform | Formatter | Message Format | Signing |
|----------|-----------|----------------|---------|
| WeChat Work | `wechat_work.py` | News cards, chunked at 8 articles | None |
| DingTalk | `dingtalk.py` | Markdown links, chunked at 20 items | Optional HMAC-SHA256 |

Feishu, Slack, and custom webhooks are not implemented in this repository.

## Adding a Platform

Create `src/formatters/my_platform.py` with:

```python
FORMATTER_VERSION = 1
MAX_ITEMS_PER_MESSAGE = 10

def format_message(changes: dict[str, list[dict]]) -> dict | None:
    ...

def send(payload: dict, webhook_url: str) -> None:
    ...
```

`send()` must raise unless both HTTP and platform-level business status confirm success. Then add `MY_PLATFORM_WEBHOOK` to both GitHub Secrets and the `Run monitor` environment in `.github/workflows/monitor.yml`. Existing pending events retain the formatter target, destination fingerprint, contract version, chunk membership, and payload captured when they were created; changing a target URL blocks old pending delivery instead of silently rerouting it.

See `src/formatters/_template.py` for the complete contract.

## Architecture

```text
src/
├── main.py              # Drain pending work, ingest snapshots, finalize events
├── sitemap.py           # Trusted fetch, canonicalization, category filtering
├── detector.py          # Snapshot guard, delta detection, durable ordering
├── outbox.py            # Stable identities, immutable chunks, receipts
├── issues.py            # Verified GitHub Issue state operations
├── enrichment.py        # Metadata fetch with redirect validation
├── notifier.py          # Formatter discovery, planning, chunk delivery
├── webhook_http.py      # Retry and business-response validation
└── formatters/
    ├── _template.py
    ├── wechat_work.py
    └── dingtalk.py
```

## Local Development

Python 3.11+ and the GitHub CLI (`gh`) are required for a full non-dry run.

```bash
pip install -r requirements.txt
git config core.hooksPath .githooks
python -m pytest tests -v
python -m src.main --dry-run
```

Commits use `<type>: <description>`, where type is one of `feat`, `fix`, `docs`, `refactor`, `test`, or `chore`.

## License

MIT
