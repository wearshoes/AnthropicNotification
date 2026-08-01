## Why

Production runs have demonstrated silent state corruption and permanent notification loss. GitHub API failures are treated as a missing baseline, notification failures are swallowed after the baseline advances, and WeChat Work truncates batches larger than eight items. The workflow reports success in these cases, so its green status is not a reliable health signal.

## What Changes

- Add a durable GitHub Issue outbox with stable per-URL item IDs, immutable target/chunk plans, and monotonic chunk receipts.
- Make all GitHub state operations fail closed with timeouts and verified return values.
- Advance baselines monotonically only after every new item is durably represented by an outbox event.
- Drain pending outbox events independently of sitemap fetching and retry failed deliveries on later runs.
- Split platform payloads without dropping items and validate platform business response codes.
- Validate sitemap origins, reject suspiciously incomplete snapshots, and prevent concurrent workflow writers.
- Reconcile documentation and specifications with the implemented platforms and at-least-once delivery semantics.

## Capabilities

### New Capabilities
- `reliable-outbox`: Durable, resumable, at-least-once notification delivery backed by GitHub Issues.

### Modified Capabilities
- `issue-state`: Fail-closed state access, monotonic baselines, and outbox-aware update lifecycle.
- `webhook-notifier`: Fixed chunk plans, platform response validation, and surfaced delivery failures.
- `sitemap-parser`: Trusted-origin filtering and incomplete-snapshot protection.
- `ci-workflow`: Single-writer concurrency and bounded job execution.
- `enriched-notifications`: Persisted payload snapshots and complete multi-message delivery.

## Impact

- New `src/outbox.py` domain model and tests.
- Changes to `src/issues.py`, `src/detector.py`, `src/main.py`, `src/notifier.py`, sitemap/enrichment, and formatters.
- Workflow, README, CODEBUDDY, and OpenSpec updates.
- Existing legacy baseline Issues require a one-time cleanup after deployment.
