## Context

GitHub Issues remain the only durable store. Webhook platforms do not support an idempotency key, so exactly-once delivery is impossible across the boundary between a successful POST and persisting its receipt. The system therefore guarantees durable at-least-once delivery: it may duplicate a chunk after a crash, but it must not silently lose one.

## Goals / Non-Goals

**Goals:**
- No GitHub API or webhook failure is interpreted as successful state progress.
- Every newly accepted URL is durably represented before the baseline advances.
- Every target and chunk is fixed when an event is created and can resume independently.
- Large batches cover every item without truncation.
- Existing pending delivery is retried even when sitemap fetching fails.

**Non-Goals:**
- Exactly-once webhook delivery.
- Replaying legacy update Issues as new notifications.
- Implementing Feishu, Slack, or Custom formatters in this change.
- Replacing GitHub Issues with an external database.

## Decisions

### 1. Stable item identity and immutable event plans

Each canonical URL receives `item_id = sha256("item/v1\\0" + category + "\\0" + url)`. An outbox event stores schema version, item IDs/URLs, a target snapshot, formatter contract versions, immutable payload chunks, and delivered chunk receipts. Event IDs identify containers; item IDs prevent overlap across crash-recovery batches.

### 2. Durable order: outbox, baseline union, delivery

For each category the system subtracts item IDs already held by pending events, persists any remaining items as outbox events, re-reads them for verification, and only then updates the baseline with `known | current`. A crash before persistence is rediscovered; a crash after persistence is resumed from pending state.

### 3. Chunk receipts are the delivery truth

After each successful platform POST, the chunk ID is appended to the event receipt set and the Issue body is updated immediately. All target chunks having receipts changes the event to delivered. Label changes and closing old display Issues are finalization only; failure there must not resend delivered chunks.

### 4. At-least-once boundary

Receipts are written after webhook success. A crash between those operations can duplicate that chunk. Writing the receipt first would permit permanent loss, so duplicates are the deliberate trade-off.

### 5. Fail-closed external operations

`gh` non-zero exits, timeouts, malformed JSON, missing issue numbers, and verification mismatches raise errors. Webhook HTTP failures and non-zero business error codes leave chunks pending and make the workflow fail after other independent targets have been attempted.

### 6. Fixed target and payload snapshots

Targets are the enabled formatters at event creation. Each target stores a non-secret SHA-256 fingerprint of its webhook URL, so a changed URL blocks old pending work instead of silently rerouting it. New formatters do not receive historical events. Missing target credentials block their existing events. Payloads and chunk membership are stored in the event, so formatter or page metadata changes do not alter retries.

### 7. Single writer and input safeguards

GitHub Actions uses one concurrency group with `cancel-in-progress: false`. Baselines are monotonic. Trusted content URLs must use HTTPS and the exact Anthropic host. Every accepted sitemap snapshot must contain all configured categories and at least 300 monitored URLs in total, including the initial snapshot.

## Risks / Trade-offs

- [Duplicate notification after crash] Accepted at-least-once behavior; receipts minimize the window.
- [Issue body limit] Event planning checks the rendered body before persistence and splits oversized events.
- [Pending target secret removed] Event remains pending and Action remains red until the credential is restored or an operator explicitly resolves it.
- [GitHub search/index lag] Workflow concurrency prevents normal races; stable item IDs and pending scans prevent overlap on recovery.
- [Schedule latency] GitHub cron remains best-effort. Documentation will state observed limitations rather than promising exact 30-minute execution.

## Migration

The new code reads legacy baseline bodies but only creates v1 outbox events for future deltas. After deployment verification, retain the newest valid baseline per category and close or relabel stale duplicates. Legacy update Issues are not replayed.
