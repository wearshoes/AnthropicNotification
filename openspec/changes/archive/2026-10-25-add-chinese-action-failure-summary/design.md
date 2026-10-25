## Context

The CLI currently catches every top-level exception, logs `Fatal error: <message>`, and exits with status 1. GitHub Actions correctly marks the job failed, but the operator must interpret an English implementation-level error from the raw log.

## Decisions

### 1. Report at the CLI boundary

The top-level handler remains the single place that turns pipeline exceptions into operator output. Core modules continue to raise typed exceptions and keep their existing recovery behavior.

### 2. Use typed, allowlisted explanations

Known snapshot, source-fetch, GitHub state, formatter, configuration, and delivery failures map to a Chinese reason and a concrete suggestion. Safe diagnostics such as snapshot counts and sanitized delivery chunk failures may be included. Arbitrary exception strings are excluded for unknown and GitHub-state failures because upstream text can contain credentials.

### 3. Target both logs and the Actions UI

Every failure is logged in Chinese. Inside GitHub Actions, the handler additionally emits an `error` workflow command and appends Markdown to `GITHUB_STEP_SUMMARY`. Workflow-command data is escaped before output.

### 4. Failure reporting is best effort

An unavailable or unwritable summary file must not replace the original pipeline failure. The process still exits non-zero after logging and annotation attempts.

## Risks / Trade-offs

- A new exception type initially receives a generic Chinese explanation. Its class name remains visible so it can be added to the allowlist later.
- GitHub annotations are concise; deeper diagnostics remain in the raw job log.
