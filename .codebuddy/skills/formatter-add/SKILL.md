---
name: formatter-add
description: Add a new notification platform formatter. Guides through the full lifecycle - OpenSpec propose, TDD implementation, workflow update, and archive.
license: MIT
metadata:
  author: project
  version: "1.0"
---

Add a new notification platform formatter with full OpenSpec + TDD workflow.

**Input**: Platform name in snake_case (e.g., `dingtalk`, `feishu`, `slack`, `custom`).

If no platform name provided, ask the user.

---

## Step 1: Derive Names and Paths

From the platform name, derive all paths and identifiers:

```
Platform: dingtalk
├── Module:     src/formatters/dingtalk.py
├── Tests:      tests/formatters/test_dingtalk.py
├── Env var:    DINGTALK_WEBHOOK
├── Secret env: DINGTALK_SECRET (if signing required)
├── Change:     add-dingtalk-formatter
└── Template:   src/formatters/_template.py (reference)
```

Announce these to the user before proceeding.

---

## Step 2: Research Platform API

Use WebFetch or WebSearch to find the platform's webhook API documentation:

- Message payload format (markdown, card, blocks, JSON)
- Authentication method (none, HMAC-SHA256, bearer token)
- Message size limits
- Rate limits
- Required fields

Summarize findings before proceeding. Key questions:
- Does it need request signing? → Need `{PLATFORM}_SECRET` env var
- What message format does it use? → Determines format_message() output
- Any size limits? → Need truncation logic

---

## Step 3: Create OpenSpec Change

```bash
openspec new change "add-{platform}-formatter"
```

Create all artifacts:

### proposal.md
- Why: Adding {platform} notification support
- What Changes: new formatter file, tests, workflow env
- New Capability: `{platform}-formatter`

### specs/{platform}-formatter/spec.md
Based on the webhook-notifier spec pattern:
- Requirement: message format (platform-specific payload)
- Requirement: send with auth (if signing needed)
- Requirement: size limits (if applicable)
- Each requirement with WHEN/THEN scenarios

### design.md
- Key decisions: message format choice, auth method, any platform quirks
- Reference existing wechat_work.py as pattern

### tasks.md
TDD order:
```
## 1. Tests
- [ ] 1.1 Write tests/formatters/test_{platform}.py

## 2. Implementation
- [ ] 2.1 Implement src/formatters/{platform}.py

## 3. Workflow + Docs
- [ ] 3.1 Add env vars to .github/workflows/monitor.yml (if missing)
- [ ] 3.2 Update CODEBUDDY.md architecture section
- [ ] 3.3 Update README.md Secret table (if missing)
- [ ] 3.4 Update README_EN.md Secret table (if missing)

## 4. Verify
- [ ] 4.1 Run full test suite

## 5. Ship
- [ ] 5.1 Commit, push, sync specs, archive change
```

---

## Step 4: TDD Implementation

### RED — Write Tests First

Read the test template for reference:
```
tests/formatters/_template_test.py
```

Create `tests/formatters/test_{platform}.py` with:

**Must-have tests:**
- `test_formats_single_category` — basic payload structure
- `test_formats_multiple_categories` — all categories in one message
- `test_empty_changes_returns_none` — guard clause
- `test_posts_to_webhook_url` — correct URL and payload
- `test_raises_on_http_error` — error propagation

**Platform-specific tests (add as needed):**
- `test_truncates_when_exceeds_limit` — if size limit exists
- `test_signs_request_with_hmac` — if signing required
- `test_includes_title_field` — if platform needs separate title
- `test_card_format_structure` — if using card/block format

Run tests, confirm RED:
```bash
python -m pytest tests/formatters/test_{platform}.py -v
```

Report: `[TDD] module={platform} step=RED tests_written=N status=FAILING`

### GREEN — Write Implementation

Read the code template for reference:
```
src/formatters/_template.py
```

Also read the existing wechat_work.py for a working example:
```
src/formatters/wechat_work.py
```

Create `src/formatters/{platform}.py` implementing:
- `format_message(changes: dict[str, set[str]]) -> dict | None`
- `send(payload: dict, webhook_url: str) -> None`

Run tests, confirm GREEN:
```bash
python -m pytest tests/formatters/test_{platform}.py -v
```

Report: `[TDD] module={platform} step=GREEN tests=N/N status=ALL PASSING`

---

## Step 5: Update Workflow

Check `.github/workflows/monitor.yml` for existing env vars. Add if missing:

```yaml
{PLATFORM}_WEBHOOK: ${{ secrets.{PLATFORM}_WEBHOOK }}
```

If signing is needed, also add:
```yaml
{PLATFORM}_SECRET: ${{ secrets.{PLATFORM}_SECRET }}
```

---

## Step 6: Update Documentation

### CODEBUDDY.md
Update the Architecture section's file tree to include the new formatter:
```
└── formatters/
    ├── ...
    └── {platform}.py   # {Platform} formatter description
```

### README.md (Chinese)
Check if the new platform's Secret is listed in the "配置 Webhook Secret" table. If not, add a row:
```
| `{PLATFORM}_WEBHOOK` | {平台}机器人 Webhook URL | 可选 |
```
If signing is needed, also add `{PLATFORM}_SECRET`.

### README_EN.md (English)
Same check and update for the English version's "Configure Webhook Secrets" table.

---

## Step 7: Verify

Run full test suite:
```bash
python -m pytest tests/ -v
```

All tests must pass before proceeding.

---

## Step 8: Commit, Push, Archive

1. Mark all tasks complete in tasks.md
2. `git add -A && git commit` with descriptive message
3. `git push`
4. Sync specs: copy `openspec/changes/{change-name}/specs/` to `openspec/specs/`
5. Archive: `mv openspec/changes/{change-name} openspec/changes/archive/YYYY-MM-DD-{change-name}`
6. Commit and push the archive
7. Inform user to add `{PLATFORM}_WEBHOOK` to GitHub Secrets to enable

---

## Guardrails

- ALWAYS read `_template.py` and `_template_test.py` before writing
- ALWAYS read `wechat_work.py` as a working reference
- NEVER skip TDD — tests MUST exist and fail before implementation
- NEVER mark tasks complete with failing tests
- Keep the formatter focused — only format_message() and send()
- Mock all HTTP calls in tests — never hit real webhooks
- If signing is complex, research the exact algorithm before writing tests
