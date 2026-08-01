## 1. Domain Model and State Safety

- [x] 1.1 Write failing tests for stable item IDs, immutable chunk plans, serialization, receipts, and body-size rejection.
- [x] 1.2 Implement `src/outbox.py` and make the domain tests pass.
- [x] 1.3 Write failing tests for GitHub command failures, timeouts, malformed responses, duplicate baselines, pending event persistence, and verification.
- [x] 1.4 Implement fail-closed Issue state and outbox persistence in `src/issues.py`.

## 2. Detection and Orchestration

- [x] 2.1 Write failing tests for pending-item subtraction, monotonic baseline union, no-target blocking, crash recovery, and pending drain when sitemap fails.
- [x] 2.2 Refactor detector/main orchestration to persist outbox before baseline progress and drain receipts independently.

## 3. Notification Delivery

- [x] 3.1 Write failing tests for 16-item WeChat chunking, fixed payload plans, partial target success, HTTP 200 business errors, and retries.
- [x] 3.2 Implement formatter planning, complete chunk delivery, response validation, and surfaced aggregate failures.

## 4. Input and Workflow Safety

- [x] 4.1 Write failing tests for untrusted sitemap origins, redirects, and incomplete category snapshots.
- [x] 4.2 Implement URL validation, redirect validation, and monotonic snapshot guards.
- [x] 4.3 Add workflow concurrency, timeout, and a test step.

## 5. Documentation and Verification

- [x] 5.1 Resolve conflicting main specs and document at-least-once semantics, actual platform support, and best-effort scheduling.
- [x] 5.2 Run full tests, coverage, dry-run, and targeted crash/failure simulations.
- [x] 5.3 Run independent adversarial subagent review and address all material findings.
- [x] 5.4 Archive the completed OpenSpec change after final local verification.
