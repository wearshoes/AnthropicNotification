## Requirements

### Requirement: Fail-closed GitHub state
All GitHub Issue reads and writes SHALL fail the run on command errors, timeouts, malformed output, missing identifiers, unexpected labels or state, or failed write verification. A failed baseline query SHALL NOT be treated as first run.

#### Scenario: Baseline query receives 401
- **WHEN** `gh issue list` exits non-zero
- **THEN** the system SHALL NOT create a replacement baseline or advance state
- **AND** the workflow SHALL fail

### Requirement: One canonical baseline per category
The newest verified open baseline SHALL be used for each category. Duplicate baselines SHALL produce a warning and SHALL NOT be combined implicitly during normal monitoring.

#### Scenario: Duplicate legacy baselines
- **WHEN** multiple verified open baselines exist for one category
- **THEN** the highest Issue number SHALL be selected
- **AND** the duplicate condition SHALL be logged

### Requirement: Verified monotonic baseline
An existing baseline SHALL only be replaced by a superset of its saved URLs. Creation and update SHALL be re-read and verified before success is reported.

#### Scenario: Partial sitemap response
- **WHEN** known URLs are `{A, B, C}` and an accepted snapshot contains `{A, X}`
- **THEN** no successful write may remove B or C

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

### Requirement: Pending-safe update lifecycle
Delivered update Issues MAY replace older delivered display Issues, but cleanup SHALL never close an Issue labeled `notification-pending`.

#### Scenario: Newer event finishes first
- **WHEN** an older update remains pending and a newer update is delivered
- **THEN** cleanup SHALL leave the older pending Issue open
