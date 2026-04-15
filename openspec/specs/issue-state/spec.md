## MODIFIED Requirements

### Requirement: Create baseline Issue
The system SHALL create labels automatically before creating issues. Labels SHALL be created idempotently using `gh label create --force`.

#### Scenario: Label does not exist
- **WHEN** the system creates a baseline Issue with label `baseline`
- **AND** label `baseline` does not exist in the repository
- **THEN** the system SHALL create the label first, then create the issue

#### Scenario: Label already exists
- **WHEN** the system creates a baseline Issue with label `baseline`
- **AND** label `baseline` already exists
- **THEN** the system SHALL skip label creation (cached) and create the issue

### Requirement: Error logging for gh CLI
The system SHALL log ERROR with stdout and stderr when any `gh` CLI command fails (non-zero exit code).

#### Scenario: gh command fails
- **WHEN** a gh CLI command returns non-zero exit code
- **THEN** the system SHALL log the command, stdout, and stderr at ERROR level

### Requirement: Create update Issue
The system SHALL create labels automatically before creating update issues, same as baseline issues.

#### Scenario: Update issue with new labels
- **WHEN** the system creates an update Issue with labels `news,update`
- **AND** these labels do not exist
- **THEN** the system SHALL create both labels first, then create the issue
