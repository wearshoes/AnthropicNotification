## ADDED Requirements

### Requirement: Durable at-least-once outbox
The system SHALL persist every newly accepted item in a pending outbox Issue before advancing its baseline. It SHALL retry pending chunks until each fixed target chunk has a durable receipt. The system SHALL NOT claim exactly-once delivery.

#### Scenario: Crash after event persistence
- **WHEN** an event is persisted and the process stops before baseline update or delivery
- **THEN** the next run SHALL reuse the persisted item IDs
- **AND** SHALL resume delivery without silently discarding an item

#### Scenario: Crash after webhook success
- **WHEN** a webhook succeeds and the process stops before its receipt is persisted
- **THEN** the chunk SHALL remain pending
- **AND** MAY be delivered again on the next run

### Requirement: Stable item and chunk identity
The system SHALL derive item IDs from a versioned canonical category and URL representation. Event targets, destination fingerprints, formatter versions, ordered chunk membership, and payloads SHALL be immutable after event creation. Planning SHALL split a batch into multiple events when one rendered Issue body would exceed the configured limit.

#### Scenario: Batch grows during recovery
- **WHEN** item X is already pending and item Y appears before the baseline advances
- **THEN** the recovery run SHALL NOT add X to a second event
- **AND** SHALL persist Y independently

#### Scenario: Oversized category delta
- **WHEN** a category delta cannot fit in one outbox Issue
- **THEN** planning SHALL create multiple complete events within the Issue body limit

#### Scenario: Destination changes during recovery
- **WHEN** a pending chunk's current webhook URL does not match its saved destination fingerprint
- **THEN** delivery SHALL remain pending and fail without sending to the new URL

### Requirement: Monotonic receipts
Each successful target chunk SHALL be recorded immediately. A recorded receipt SHALL never return to pending. Event finalization failures SHALL NOT resend receipted chunks.

#### Scenario: One target partially fails
- **WHEN** target A chunk 1 succeeds, target A chunk 2 fails, and target B succeeds
- **THEN** receipts SHALL be stored for A chunk 1 and all B chunks
- **AND** the next run SHALL retry only A chunk 2
