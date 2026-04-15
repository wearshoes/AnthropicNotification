# Anthropic Notification

English | [中文](README.md)

Monitor [Anthropic](https://www.anthropic.com) website for new content and receive webhook notifications.

## Features

- **Sitemap-based** change detection — stable and reliable, no dependency on HTML structure
- **GitHub Issues** as state storage — no database or external services needed
- Multi-platform **Webhook notifications** (WeChat Work, DingTalk, Feishu, Slack, Custom)
- **GitHub Actions** automation, checks every 30 minutes
- Convention-based **Formatter discovery** — add a notification platform by adding one file
- Silent baseline creation on first run — no notification flood

## How It Works

```
                    ┌──────────────┐
                    │ Sitemap.xml  │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │ Filter by    │  news / research / engineering / learn
                    │ category     │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐     ┌──────────────┐
                    │ Compare with │◄────│ GitHub Issues│
                    │ baseline     │     │ (state store)│
                    └──────┬───────┘     └──────────────┘
                           │
                    ┌──────▼───────┐
                    │ New content  │
                    │ found        │
                    └──────┬───────┘
                           │
                ┌──────────┼──────────┐
                ▼          ▼          ▼
         Create Issue  Update     Send Webhook
         (record)     baseline    (notify)
```

1. Fetches `https://www.anthropic.com/sitemap.xml` every 30 minutes via GitHub Actions
2. Filters URLs into 4 categories: news, research, engineering, learn
3. Compares against baseline URLs stored in GitHub Issues
4. For new URLs: creates an Issue + sends aggregated webhook notification
5. First run silently creates the baseline (no notifications)

## Monitored Pages

| Category | URL Pattern | Content |
|----------|-------------|---------|
| news | `/news/*` | Product launches, company announcements |
| research | `/research/*` | AI safety papers, technical reports |
| engineering | `/engineering/*` | Engineering blog posts |
| learn | `/learn/*` | Anthropic Academy courses |

## Quick Start

### Step 1: Fork This Repository

Click the **Fork** button at the top right of this repository.

### Step 2: Configure Webhook Secrets

1. Go to your forked repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add the webhook URL(s) for your notification platforms:

| Secret Name | Description | Required |
|-------------|-------------|----------|
| `WECHAT_WORK_WEBHOOK` | WeChat Work bot webhook URL | At least one |
| `DINGTALK_WEBHOOK` | DingTalk custom robot webhook URL | Optional |
| `DINGTALK_SECRET` | DingTalk robot signing secret | Optional |
| `FEISHU_WEBHOOK` | Feishu/Lark custom bot webhook URL | Optional |
| `FEISHU_SECRET` | Feishu bot signing secret | Optional |
| `SLACK_WEBHOOK` | Slack incoming webhook URL | Optional |
| `CUSTOM_WEBHOOK` | Any custom webhook endpoint | Optional |

> A notification channel is automatically enabled when its webhook secret is set. No additional configuration needed.

### Step 3: Enable GitHub Actions

1. Go to the **Actions** tab in your forked repository
2. If you see "Workflows aren't being run on this forked repository", click **I understand my workflows, go ahead and enable them**
3. Find **Monitor Anthropic Website** workflow
4. Click **Run workflow** → **Run workflow** to trigger manually

### Step 4: Verify

The first run will:
- Create 4 baseline Issues ([Baseline] news / research / engineering / learn)
- **Not send any notifications** (expected — silent baseline creation)

After that, it checks every 30 minutes. When Anthropic publishes new content, you will:
- Receive a webhook notification
- See a new update Issue in your repository

## Adding a Notification Platform

Create a new Python file in `src/formatters/`:

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

Then add `MY_PLATFORM_WEBHOOK` to GitHub Secrets.

The system auto-discovers formatters: filename `my_platform.py` maps to env var `MY_PLATFORM_WEBHOOK`.

## Architecture

```
src/
├── main.py              # Orchestrator: sitemap → detector → issues → notifier
├── sitemap.py           # Fetch and parse sitemap.xml, filter by category
├── detector.py          # Compare sitemap URLs vs baseline, find new content
├── issues.py            # GitHub Issues management via gh CLI (baseline + updates)
├── notifier.py          # Convention-based formatter discovery + dispatch
└── formatters/
    └── wechat_work.py   # WeChat Work markdown formatter

tests/                   # Unit tests (pytest, 45 tests)
.github/workflows/
    └── monitor.yml      # GitHub Actions workflow (every 30 minutes)
```

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/ -v

# Fetch sitemap only (no detection or notification)
python -m src.main --dry-run
```

## License

MIT
