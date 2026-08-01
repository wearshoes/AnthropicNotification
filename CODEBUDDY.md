# CODEBUDDY.md

This repository monitors Anthropic's sitemap, stores durable state in GitHub Issues, and sends WeChat Work or DingTalk webhook notifications.

## Compound Interest Principle

- Prefer reusable assets over one-off fixes.
- Deliver end-to-end slices that make later work cheaper.
- Extract a shared pattern when it repeats.
- Evaluate changes against the reliability contract below, not only the happy path.

## Required Development Workflow

All code changes follow:

1. Explore the behavior and failure modes.
2. Create an OpenSpec change with proposal, specs, design, and tasks.
3. Apply with strict TDD: RED, GREEN, REFACTOR.
4. Sync main specs and archive the completed change.

### Repository Guards

- `tdd-guard.sh` requires the corresponding test before writing `src/**/*.py`.
- `tdd-autotest.sh` runs pytest after source edits.
- `openspec-guard.sh` checks for an active OpenSpec change.
- `.githooks/commit-msg` requires `<type>: <description>`.
- Valid commit types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`.

## Reliability Contract

The system guarantees durable at-least-once delivery, not exactly-once delivery.

Required state order:

```text
persist and verify outbox event
    -> write and verify monotonic baseline union
    -> deliver fixed payload chunks
    -> write and verify each receipt
    -> finalize labels and display Issues
```

- `item_id` is stable per versioned category and canonical URL.
- An event snapshots targets, non-secret destination fingerprints, formatter versions, item ordering, chunk membership, and payloads.
- Planning recursively splits batches that would exceed the GitHub Issue body limit.
- A receipted chunk is never sent again.
- A crash after webhook success but before receipt persistence may duplicate that chunk.
- Every GitHub command error, timeout, malformed response, or failed verification aborts state progress.
- A new delta with no enabled formatter is blocked before outbox creation or baseline progress.
- Pending events repair their category baseline before delivery and drain before sitemap fetching.
- Baselines only grow; every accepted sitemap snapshot has all configured categories non-empty and at least 300 monitored URLs in total.
- Workflow concurrency provides one Issue-state writer.

## Architecture

```text
src/
├── main.py              # Pending recovery, snapshot ingestion, finalization
├── sitemap.py           # Trusted fetch, canonicalization, category filtering
├── detector.py          # Snapshot guard and outbox-before-baseline ordering
├── outbox.py            # Stable IDs, fixed chunks, serialization, receipts
├── issues.py            # Fail-closed and verified GitHub Issue operations
├── enrichment.py        # Metadata snapshot with redirect validation
├── notifier.py          # Formatter discovery, event planning, chunk delivery
├── webhook_http.py      # Bounded retry and business-status validation
└── formatters/
    ├── _template.py
    ├── wechat_work.py
    └── dingtalk.py
```

## Formatter Contract

`src/formatters/{name}.py` maps to `{NAME}_WEBHOOK`. Files starting with `_` are not discovered.

Each formatter exports:

```python
FORMATTER_VERSION = 1
MAX_ITEMS_PER_MESSAGE = 10

def format_message(changes: dict[str, list[dict]]) -> dict | None: ...
def send(payload: dict, webhook_url: str) -> None: ...
```

- `format_message()` receives one bounded enriched chunk.
- `send()` returns only after HTTP and platform business status both confirm success.
- Adding a formatter also requires its webhook environment variable in `.github/workflows/monitor.yml`.
- A formatter contract change increments `FORMATTER_VERSION`; old pending versions must remain supportable or be resolved explicitly.
- Changing a webhook URL changes its destination fingerprint and blocks delivery of old pending chunks.

## GitHub Issues

- Baseline labels: `baseline,{category}`.
- Pending outbox labels: `{category},update,notification-pending`.
- Delivered outbox label: `notification-delivered`.
- Issue bodies contain a human-readable section and a machine-owned JSON marker.
- Never edit or truncate the machine marker manually.
- Cleanup must never close an Issue still labeled `notification-pending`.

## Tests

- `src/{module}.py` maps to `tests/test_{module}.py`.
- `src/formatters/{name}.py` maps to `tests/formatters/test_{name}.py`.
- Mock external HTTP and subprocess calls.
- Cover crash windows, partial target success, business-level webhook errors, and write verification.

```bash
python -m pytest tests -v
python -m pytest tests --cov=src --cov-report=term-missing
python -m src.main --dry-run
python -m src.main  # requires gh and GH_TOKEN
```

## Adding a Category

1. Add its path prefix to `CATEGORIES` in `src/sitemap.py`.
2. Write sitemap and snapshot-guard tests first.
3. Update both READMEs and OpenSpec.
4. Ensure first-run and empty-category baseline behavior remains explicit.

## OpenSpec

Main specs live in `openspec/specs/`. Completed changes move to `openspec/changes/archive/` only after delta specs are synced and verification passes.
