# Anthropic Notification

Monitor [Anthropic](https://www.anthropic.com) website for new content and receive webhook notifications.

## How It Works

```
Sitemap.xml ──→ Filter by category ──→ Compare with baseline ──→ New URLs found?
                                              │                        │
                                       GitHub Issues             Create Issue
                                       (state store)          + Send Webhook
```

1. Fetches `https://www.anthropic.com/sitemap.xml` every 6 hours via GitHub Actions
2. Filters URLs into categories: `news`, `research`, `engineering`, `learn`
3. Compares against baseline stored in GitHub Issues
4. For new URLs: creates an Issue and sends webhook notifications
5. First run silently creates the baseline (no notification flood)

## Monitored Pages

| Category | URL Pattern | Content |
|----------|-------------|---------|
| news | `/news/*` | Product launches, company announcements |
| research | `/research/*` | AI safety papers, technical reports |
| engineering | `/engineering/*` | Engineering blog posts |
| learn | `/learn/*` | Anthropic Academy courses |

## Setup

### 1. Fork this repository

### 2. Configure Secrets

Go to **Settings → Secrets and variables → Actions** and add:

| Secret | Required | Description |
|--------|----------|-------------|
| `WECHAT_WORK_WEBHOOK` | No | WeChat Work bot webhook URL |
| `DINGTALK_WEBHOOK` | No | DingTalk robot webhook URL |
| `DINGTALK_SECRET` | No | DingTalk signing secret |
| `FEISHU_WEBHOOK` | No | Feishu/Lark bot webhook URL |
| `FEISHU_SECRET` | No | Feishu signing secret |
| `SLACK_WEBHOOK` | No | Slack incoming webhook URL |
| `CUSTOM_WEBHOOK` | No | Any custom webhook endpoint |

A notification channel is **automatically enabled** when its webhook secret is set. No other configuration needed.

### 3. Enable GitHub Actions

The workflow runs automatically every 6 hours. You can also trigger it manually from the **Actions** tab.

## Adding a Notification Platform

Drop a new Python file in `src/formatters/`:

```
src/formatters/my_platform.py
```

The file must export two functions:

```python
def format_message(changes: dict[str, set[str]]) -> dict | None:
    """Format changes into platform-specific payload."""
    ...

def send(payload: dict, webhook_url: str) -> None:
    """Send payload to the webhook."""
    ...
```

Set the environment variable `MY_PLATFORM_WEBHOOK` — the system discovers formatters by convention: filename `my_platform.py` maps to env var `MY_PLATFORM_WEBHOOK`.

## Local Development

```bash
pip install -r requirements.txt
python -m pytest tests/ -v          # Run tests
python -m src.main --dry-run        # Fetch sitemap without detection/notification
```

## Architecture

```
src/
├── main.py          # Orchestrator: sitemap → detector → issues → notifier
├── sitemap.py       # Fetch and parse sitemap.xml, filter by category
├── detector.py      # Compare sitemap URLs vs baseline, find new content
├── issues.py        # GitHub Issues API via gh CLI (baseline + update issues)
├── notifier.py      # Convention-based formatter discovery + dispatch
└── formatters/
    └── wechat_work.py   # WeChat Work markdown formatter
```

## License

MIT
