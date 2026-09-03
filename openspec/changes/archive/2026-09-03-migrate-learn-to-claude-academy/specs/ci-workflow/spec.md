## MODIFIED Requirements

### Requirement: Immutable supported action references
Every third-party GitHub Action SHALL be referenced by a full commit SHA from a maintained release whose runtime is supported by the GitHub-hosted runner.

#### Scenario: Action runtime is deprecated
- **WHEN** a pinned Action release targets a deprecated runtime
- **THEN** the repository SHALL update to a reviewed maintained release
- **AND** SHALL continue pinning the reference to its full commit SHA
