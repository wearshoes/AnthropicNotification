## MODIFIED Requirements

### Requirement: Scheduled execution
The workflow SHALL run on a cron schedule every 30 minutes and support manual trigger via `workflow_dispatch`. Additionally it SHALL trigger on push to main when the workflow file itself changes.

#### Scenario: Cron trigger
- **WHEN** the cron schedule fires every 30 minutes
- **THEN** the workflow SHALL execute the monitoring script

#### Scenario: Push trigger on workflow change
- **WHEN** `.github/workflows/monitor.yml` is modified and pushed to main
- **THEN** the workflow SHALL execute
