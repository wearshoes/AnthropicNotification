## MODIFIED Requirements

### Requirement: Fail-closed GitHub state
All GitHub Issue reads and writes SHALL fail the run on command errors, timeouts, malformed output, unexpected labels or state, or failed verification. A failed baseline query SHALL NOT be treated as first run.

#### Scenario: Baseline query receives 401
- **WHEN** `gh issue list` exits non-zero
- **THEN** the category SHALL NOT create a baseline or advance state
- **AND** the workflow SHALL fail

### Requirement: Monotonic baseline
An existing baseline SHALL be updated with the union of known and current trusted URLs only after all newly accepted items are durably stored in the outbox.

#### Scenario: Partial sitemap response
- **WHEN** known URLs are `{A, B, C}` and a permitted snapshot contains `{A, X}`
- **THEN** no successful state transition may remove B or C

## ADDED Requirements

### Requirement: Recoverable machine outbox discovery
The system SHALL inspect every page of machine-owned update Issues independently of the mutable pending label. A valid open outbox whose pending label was removed SHALL have that label restored and SHALL remain eligible for recovery.

#### Scenario: Pending label removed manually
- **WHEN** a valid open outbox body is pending but `notification-pending` is absent
- **THEN** the system SHALL restore and verify the pending label before delivery continues

### Requirement: Conflicting pending ownership
The system SHALL quarantine every pending outbox Issue that shares an item ID with another pending owner. It SHALL continue processing unrelated pending Issues and SHALL fail the run while any ownership conflict remains.

#### Scenario: Duplicate owner beside independent work
- **WHEN** two pending Issues own item X and a third pending Issue owns only item Y
- **THEN** neither owner of X SHALL be delivered
- **AND** the Issue containing Y SHALL remain eligible for delivery
- **AND** the workflow SHALL fail
