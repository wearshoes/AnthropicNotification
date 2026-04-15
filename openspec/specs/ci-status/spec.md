## ADDED Requirements

### Requirement: Auto-query CI status after push
A PostToolUse hook on Bash SHALL detect git push commands and automatically query GitHub Actions for the latest workflow run status.

#### Scenario: Push detected with GITHUB_TOKEN
- **WHEN** a Bash command containing `git push` completes
- **AND** `GITHUB_TOKEN` environment variable is set
- **THEN** the hook SHALL query the latest Actions run and return status as additionalContext

#### Scenario: Push detected without GITHUB_TOKEN
- **WHEN** a Bash command containing `git push` completes
- **AND** `GITHUB_TOKEN` is NOT set
- **THEN** the hook SHALL skip silently (exit 0)

#### Scenario: Non-push Bash commands
- **WHEN** a Bash command not containing `git push` completes
- **THEN** the hook SHALL not trigger any CI query
