## MODIFIED Requirements

### Requirement: Persisted payload snapshot
Enriched payloads SHALL be stored in immutable outbox chunks before baseline progress. Retry SHALL use the stored payload rather than enrich or format the URL again.

#### Scenario: Page changes during retry
- **WHEN** an outbox event remains pending after its source page changes
- **THEN** the retry SHALL send the payload captured when the event was created

### Requirement: Complete WeChat Work news delivery
WeChat Work SHALL use `msgtype: news` with no more than 8 articles per payload and SHALL create further chunks for remaining items.

#### Scenario: More than eight articles
- **WHEN** 16 enriched items target WeChat Work
- **THEN** all 16 SHALL be represented across two fixed chunks
