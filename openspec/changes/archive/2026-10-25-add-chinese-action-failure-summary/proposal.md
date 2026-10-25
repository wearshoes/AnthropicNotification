## Why

Monitor failures currently end with a short English exception such as `Sitemap snapshot is incomplete`, which does not tell a Chinese-speaking operator what stopped, whether state was protected, or what to check next. Repeated scheduled failures are therefore harder to diagnose from the GitHub Actions list.

## What Changes

- Classify expected pipeline failures into concise Chinese reasons and recovery suggestions.
- Emit a GitHub Actions error annotation so the reason is visible without expanding every log line.
- Append the same structured explanation to the GitHub Actions step summary.
- Include only allowlisted technical details and suppress arbitrary exception text that could contain credentials.
- Preserve the non-zero process exit and existing fail-closed behavior.

## Capabilities

### Modified Capabilities
- `ci-workflow`: Make failed production runs explain their cause and next action in Chinese.

## Impact

- Changes to `src/main.py`, orchestration tests, bilingual documentation, and the CI workflow specification.
- No changes to scheduling, Issue lifecycle, notification delivery semantics, or successful-run output.
