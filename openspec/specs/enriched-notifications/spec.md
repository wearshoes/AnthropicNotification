## Requirements

### Requirement: Trusted page metadata enrichment
The system SHALL fetch each new trusted URL and snapshot title, description, and image metadata. Redirect targets SHALL be validated before following. Fetch failure SHALL fall back to a slug title with no description or image.

#### Scenario: Metadata fetch fails
- **WHEN** a page times out or attempts a cross-origin redirect
- **THEN** enrichment SHALL return the original URL and slug title
- **AND** SHALL NOT prevent durable planning

### Requirement: Persisted payload snapshot
Enriched payloads SHALL be persisted in immutable outbox chunks before delivery. A retry SHALL use the persisted payload instead of fetching or formatting the page again.

#### Scenario: Page metadata changes during retry
- **WHEN** an event is pending and the source page later changes
- **THEN** the retry SHALL send the payload captured by the event

### Requirement: WeChat Work news format
WeChat Work SHALL use `msgtype: news` with at most 8 articles per payload. Batches larger than 8 SHALL create additional payload chunks rather than truncate items.

#### Scenario: Sixteen enriched articles
- **WHEN** 16 items target WeChat Work
- **THEN** two 8-article chunks SHALL be persisted
