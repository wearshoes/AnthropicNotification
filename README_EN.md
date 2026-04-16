# Anthropic Notification

English | [中文](README.md)

Monitor [Anthropic](https://www.anthropic.com) website for new content and receive webhook notifications.

## Features

- **Sitemap-based** change detection — stable and reliable, no dependency on HTML structure
- **GitHub Issues** as state storage — no database or external services needed
- Multi-platform **Webhook notifications** (WeChat Work, DingTalk, Feishu, Slack, Custom)
- **Page metadata enrichment**: auto-fetches article title, description, and cover image for richer notifications
- **GitHub Actions** automation, checks every 30 minutes
- Convention-based **Formatter discovery** — add a notification platform by adding one file
- **Issue lifecycle management**: only keeps the latest update issue per category, auto-closes old ones
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
              ┌────────────┼────────────┐
              ▼            ▼            ▼
       Create agg.    Update       Enrich metadata
       Issue          baseline     + Send webhook
       (close old)    (add URLs)   (title/desc/image)
```

1. Fetches `https://www.anthropic.com/sitemap.xml` every 30 minutes via GitHub Actions
2. Filters URLs into 4 categories
3. Compares against baseline URLs stored in GitHub Issues
4. For new URLs:
   - Creates one aggregated Issue per category, auto-closes old update Issues
   - Fetches each page's title/description/image metadata
   - Sends rich notifications with cover images and article titles
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
- Receive a rich notification with cover image and article title
- See an aggregated update Issue (old ones per category auto-closed)

## Supported Platforms

| Platform | Formatter | Message Format | Signing |
|----------|-----------|---------------|---------|
| WeChat Work | `wechat_work.py` | News card (image + title) | None |
| DingTalk | `dingtalk.py` | Markdown link list | HMAC-SHA256 (optional) |

## Adding a Notification Platform

Create a new Python file in `src/formatters/`:

```
src/formatters/my_platform.py
```

The file must export two functions:

```python
def format_message(changes: dict[str, list[dict]]) -> dict | None:
    """Format changes into platform-specific payload.
    
    changes format: {"news": [{"url": "...", "title": "...", "description": "...", "image": "..."}]}
    """
    ...

def send(payload: dict, webhook_url: str) -> None:
    """Send payload to the webhook."""
    ...
```

Then add `MY_PLATFORM_WEBHOOK` to GitHub Secrets.

The system auto-discovers formatters: filename `my_platform.py` maps to env var `MY_PLATFORM_WEBHOOK`.

See `src/formatters/_template.py` for the full interface contract, and `src/formatters/_styles/` for message style catalogs per platform.

## Architecture

```
src/
├── main.py              # Orchestrator: sitemap → detector → issues → notifier
├── sitemap.py           # Fetch and parse sitemap.xml, filter by category
├── detector.py          # Compare sitemap URLs vs baseline, find new content
├── issues.py            # GitHub Issues via gh CLI (baseline + updates + auto-close)
├── enrichment.py        # Fetch page metadata (og:title, og:description, og:image)
├── notifier.py          # Convention-based formatter discovery + enrichment + dispatch
└── formatters/
    ├── _template.py     # Formatter code template
    ├── _styles/         # Message style catalogs per platform
    │   ├── wechat_work.md
    │   ├── dingtalk.md
    │   ├── feishu.md
    │   └── slack.md
    ├── wechat_work.py   # WeChat Work news card formatter
    └── dingtalk.py      # DingTalk markdown formatter (HMAC-SHA256 signing)

tests/                   # Unit tests (pytest, 68 tests)
.github/workflows/
    └── monitor.yml      # GitHub Actions workflow (every 30 minutes)
.githooks/
    └── commit-msg       # Git commit message format validation
```

## CodeBuddy Skills

This project integrates [CodeBuddy Code](https://cnb.cool/codebuddy/codebuddy-code) Skills for automated development workflows:

| Command | Description |
|---------|-------------|
| `/formatter:add <platform>` | Add a notification platform with full OpenSpec + TDD workflow, including message style selection |
| `/category:add <name> <path>` | Add a monitored category, updating code + tests + docs |
| `/opsx:explore` | Enter explore mode — think through problems with compound interest lens |
| `/opsx:propose` | Create an OpenSpec change proposal (proposal → specs → design → tasks) |
| `/opsx:apply` | Implement change tasks with TDD (RED → GREEN → REFACTOR) |
| `/opsx:archive` | Archive change, sync specs, commit and push |

### Workflow Guard Hooks

| Hook | Type | Purpose |
|------|------|---------|
| `tdd-guard.sh` | PreToolUse | Requires test file before writing to src/ |
| `tdd-autotest.sh` | PostToolUse | Auto-runs pytest after writing src/ files |
| `openspec-guard.sh` | PreToolUse | Reminds to create OpenSpec change before modifying src/ |
| `ci-status.sh` | PostToolUse | Auto-queries GitHub Actions status after git push |
| `commit-msg` | Git Hook | Enforces `<type>: <description>` commit format |

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Configure git hooks (commit message validation)
git config core.hooksPath .githooks

# Run tests
python -m pytest tests/ -v

# Fetch sitemap only (no detection or notification)
python -m src.main --dry-run
```

### Commit Convention

```
<type>: <description>

type: feat | fix | docs | refactor | test | chore
```

## License

MIT
