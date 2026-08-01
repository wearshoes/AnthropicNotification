## MODIFIED Requirements

### Requirement: Single bounded monitor writer
The workflow SHALL serialize monitor runs through one concurrency group without cancelling an active writer. The monitor job SHALL have a finite timeout and SHALL run tests before production execution on workflow changes.

#### Scenario: Schedule and manual trigger overlap
- **WHEN** a scheduled run is active and a manual run starts
- **THEN** only one run SHALL mutate Issue state at a time

## ADDED Requirements

### Requirement: Immutable action references
Every third-party GitHub Action SHALL be referenced by a full commit SHA.

#### Scenario: Action major tag moves
- **WHEN** an upstream action changes a movable major-version tag
- **THEN** the monitor SHALL continue using its reviewed commit until this repository updates it explicitly
