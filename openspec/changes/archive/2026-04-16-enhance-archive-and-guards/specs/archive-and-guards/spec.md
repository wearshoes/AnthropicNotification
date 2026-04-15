## ADDED Requirements

### Requirement: Archive auto-sync and push
The `/opsx:archive` skill SHALL automatically sync delta specs to main specs, commit all changes, and push to remote after archiving.

#### Scenario: Archive with specs sync
- **WHEN** user runs `/opsx:archive` on a completed change
- **THEN** the skill SHALL sync delta specs to `openspec/specs/`, move the change to archive, commit, and push

### Requirement: OpenSpec guard hook
A PreToolUse hook SHALL check for an active OpenSpec change before allowing modifications to `src/**/*.py` files. The hook SHALL use `ask` mode (prompt confirmation, not hard block).

#### Scenario: No active change exists
- **WHEN** agent tries to write to `src/detector.py`
- **AND** no active OpenSpec change exists
- **THEN** the hook SHALL return `permissionDecision: "ask"` with a warning message

#### Scenario: Active change exists
- **WHEN** agent tries to write to `src/detector.py`
- **AND** an active OpenSpec change exists
- **THEN** the hook SHALL allow the write silently

#### Scenario: Non-src files are not guarded
- **WHEN** agent writes to files outside `src/` (e.g., README.md, .codebuddy/)
- **THEN** the hook SHALL not trigger

### Requirement: Commit message format
A git commit-msg hook SHALL enforce the format `<type>: <description>` where type is one of: feat, fix, docs, refactor, test, chore.

#### Scenario: Valid commit message
- **WHEN** commit message is `feat: add dingtalk formatter`
- **THEN** the hook SHALL allow the commit (exit 0)

#### Scenario: Invalid commit message
- **WHEN** commit message is `added stuff`
- **THEN** the hook SHALL reject the commit (exit 1) with an error explaining the required format

#### Scenario: Merge commits are exempt
- **WHEN** commit message starts with `Merge`
- **THEN** the hook SHALL allow the commit
