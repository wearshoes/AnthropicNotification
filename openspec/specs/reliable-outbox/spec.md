## Requirements

### Requirement: Durable at-least-once outbox
The system SHALL persist each newly accepted item in a pending outbox Issue before advancing its baseline. It SHALL retry fixed target chunks until every chunk has a durable receipt. It SHALL NOT claim exactly-once delivery.

#### Scenario: Crash after event persistence
- **WHEN** an event is persisted and the process stops before baseline update or delivery
- **THEN** the next run SHALL recognize the persisted item IDs
- **AND** SHALL resume delivery without silently discarding an item

#### Scenario: Crash after webhook success
- **WHEN** a webhook succeeds and the process stops before its receipt is persisted
- **THEN** the chunk SHALL remain pending
- **AND** MAY be delivered again on the next run

### Requirement: Stable item and chunk identity
The system SHALL derive item IDs from a versioned category and canonical URL representation. Event targets, destination fingerprints, formatter versions, ordered chunk membership, and payloads SHALL be fixed when the event is created. Planning SHALL split a batch into multiple events when one rendered Issue body would exceed the configured limit.

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
Each successful target chunk SHALL be recorded immediately. A recorded receipt SHALL never return to pending. Finalization failures SHALL NOT resend receipted chunks.

#### Scenario: Independent target failure
- **WHEN** target A fails and target B succeeds
- **THEN** B's receipt SHALL be saved
- **AND** a later run SHALL retry A without resending B
