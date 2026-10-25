## Requirements

### Requirement: Best-effort scheduled execution
The workflow SHALL request execution every 30 minutes and support manual execution. Documentation SHALL describe GitHub's cron scheduling as best-effort rather than guaranteed.

#### Scenario: Manual trigger
- **WHEN** a user invokes `workflow_dispatch`
- **THEN** the monitor workflow SHALL execute

### Requirement: Single bounded monitor writer
All monitor triggers SHALL share one concurrency group with active-run cancellation disabled. The monitor job SHALL have a finite timeout and SHALL run tests before production execution.

#### Scenario: Schedule and manual trigger overlap
- **WHEN** a scheduled run is active and a manual run starts
- **THEN** only one run SHALL mutate Issue state at a time

### Requirement: Minimum permissions and implemented secrets
The workflow SHALL request only `issues: write` and `contents: read`. It SHALL inject credentials only for notification platforms implemented by the repository.

#### Scenario: Unsupported platform secret
- **WHEN** no formatter implementation exists for a platform
- **THEN** the workflow SHALL NOT imply support by injecting that platform's secret

### Requirement: Immutable supported action references
Every third-party GitHub Action SHALL be referenced by a full commit SHA from a maintained release whose runtime is supported by the GitHub-hosted runner.

#### Scenario: Action major tag moves
- **WHEN** an upstream action changes a movable major-version tag
- **THEN** the monitor SHALL continue using its reviewed commit until this repository updates it explicitly

#### Scenario: Action runtime is deprecated
- **WHEN** a pinned Action release targets a deprecated runtime
- **THEN** the repository SHALL update to a reviewed maintained release
- **AND** SHALL continue pinning the reference to its full commit SHA

### Requirement: Chinese operator-facing failure report
When the production monitor exits because of an exception, it SHALL preserve the non-zero exit and emit a concise Chinese reason and recovery suggestion. Known safe diagnostics SHALL identify the failed condition without requiring the operator to infer it from a traceback.

#### Scenario: Snapshot completeness guard rejects upstream content
- **WHEN** the fetched snapshot is incomplete
- **THEN** the failure output SHALL explain in Chinese that the safety guard stopped the run
- **AND** SHALL include the safe total and empty-category diagnostic

#### Scenario: Unknown exception reaches the CLI boundary
- **WHEN** an unclassified exception reaches the top-level handler
- **THEN** the output SHALL provide a generic Chinese failure reason and the exception class name
- **AND** SHALL NOT include the arbitrary exception message

### Requirement: GitHub Actions surfaces the failure reason
Inside GitHub Actions, the CLI SHALL emit an escaped `error` workflow annotation and append a Markdown failure report to `GITHUB_STEP_SUMMARY`. Failure-reporting errors SHALL NOT replace the original pipeline failure.

#### Scenario: GitHub summary file is available
- **WHEN** a production failure occurs with `GITHUB_ACTIONS=true` and `GITHUB_STEP_SUMMARY` set
- **THEN** the run SHALL contain a Chinese error annotation
- **AND** the step summary SHALL contain the reason, recovery suggestion, and allowlisted technical detail

#### Scenario: Summary file cannot be written
- **WHEN** appending the step summary raises an operating-system error
- **THEN** the CLI SHALL log a warning and still exit non-zero for the original failure

### Requirement: Failure reports do not expose arbitrary sensitive text
The reporter SHALL include exception text only for explicitly allowlisted exception types whose messages are designed to be safe. GitHub state errors and unknown exceptions SHALL expose only their type and the mapped operator guidance.

#### Scenario: Unknown exception contains a credential
- **WHEN** an unknown exception message contains a webhook URL or token
- **THEN** neither the Actions annotation nor step summary SHALL contain that message
