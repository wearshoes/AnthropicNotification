## ADDED Requirements

### Requirement: Taxonomy migration preserves notification meaning
When an upstream URL taxonomy change moves or resurfaces historical content, the operator SHALL monotonically seed verified target baselines before deploying the new classifier. Genuinely new content published during the outage SHALL remain unseeded and SHALL be delivered through the durable outbox.

#### Scenario: Existing engineering URL moves to research path
- **WHEN** an existing engineering article redirects to a new canonical URL that remains classified as engineering
- **THEN** the new canonical URL SHALL be unioned into the engineering baseline before deployment
- **AND** the move SHALL NOT produce a notification

#### Scenario: New content appears during outage
- **WHEN** an article was newly published during the interval after the last successful snapshot
- **THEN** the article SHALL NOT be included in the migration seed
- **AND** normal detection SHALL create and deliver an outbox event after deployment
