## 1. Specification and Tests

- [x] 1.1 Define Chinese failure reporting, Actions presentation, and secret-safety requirements.
- [x] 1.2 Add failing tests for typed Chinese explanations, unknown-error redaction, workflow-command escaping, and step-summary output.

## 2. Implementation

- [x] 2.1 Implement typed failure descriptions at the CLI boundary.
- [x] 2.2 Emit a GitHub error annotation and append a structured step summary without masking the original failure.
- [x] 2.3 Update bilingual documentation and the main CI workflow specification.

## 3. Verification

- [x] 3.1 Run focused and full tests, coverage, strict OpenSpec validation, and dry-run.
- [x] 3.2 Push and verify a successful production Action remains unchanged, then archive the change.
