## ADDED Requirements

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
