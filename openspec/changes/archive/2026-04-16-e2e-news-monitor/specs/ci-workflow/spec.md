## ADDED Requirements

### Requirement: Scheduled execution
The workflow SHALL run on a cron schedule every 6 hours (UTC 00:00, 06:00, 12:00, 18:00) and support manual trigger via `workflow_dispatch`.

#### Scenario: Cron trigger
- **WHEN** the cron schedule fires
- **THEN** the workflow SHALL execute the monitoring script

#### Scenario: Manual trigger
- **WHEN** a user triggers `workflow_dispatch`
- **THEN** the workflow SHALL execute the monitoring script

### Requirement: Inject secrets as environment variables
The workflow SHALL pass all notification webhook secrets as environment variables to the Python script. The naming convention SHALL be `<PLATFORM>_WEBHOOK` and `<PLATFORM>_SECRET`.

#### Scenario: Secret exists
- **WHEN** GitHub Secret `WECHAT_WORK_WEBHOOK` is configured
- **THEN** the environment variable `WECHAT_WORK_WEBHOOK` SHALL be available to the script

#### Scenario: Secret does not exist
- **WHEN** GitHub Secret `WECHAT_WORK_WEBHOOK` is not configured
- **THEN** the environment variable `WECHAT_WORK_WEBHOOK` SHALL be empty or unset

### Requirement: Permissions
The workflow SHALL request only the minimum required permissions: `issues: write` for Issue management, `contents: read` for checkout.

#### Scenario: Issue creation succeeds
- **WHEN** the script creates an Issue via `gh` CLI
- **THEN** it SHALL succeed with the granted `GITHUB_TOKEN` permissions
