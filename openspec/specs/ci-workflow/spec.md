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
