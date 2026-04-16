## MODIFIED Requirements

### Requirement: Create update Issue (aggregated)
The system SHALL create ONE update Issue per category per run, aggregating all new URLs into a single issue body. The title SHALL indicate the count and category.

#### Scenario: Multiple new URLs in same category
- **WHEN** 3 new URLs are found for category `news`
- **THEN** the system SHALL create ONE issue with title `[News] 3 new updates`
- **AND** the body SHALL list all 3 URLs with their slugs

#### Scenario: Single new URL
- **WHEN** 1 new URL is found for category `news`
- **THEN** the system SHALL create ONE issue with title `[News] article-slug`
- **AND** the body SHALL contain the URL and discovery timestamp

### Requirement: Close old update Issues
After creating a new update Issue for a category, the system SHALL close all previously open update Issues for that same category. Baseline Issues SHALL never be closed.

#### Scenario: Old update issues exist
- **WHEN** a new update Issue is created for category `news`
- **AND** there are 2 previously open Issues with labels `news,update`
- **THEN** the system SHALL close those 2 old Issues

#### Scenario: No old update issues
- **WHEN** a new update Issue is created for category `news`
- **AND** there are no previously open Issues with labels `news,update`
- **THEN** no close operations are performed

#### Scenario: Baseline Issues are never closed
- **WHEN** the system searches for old update Issues to close
- **THEN** it SHALL only match Issues with BOTH labels `{category}` AND `update`
- **AND** SHALL NOT close Issues with label `baseline`

### Requirement: Issue count steady state
At steady state, the maximum number of open Issues SHALL be: 4 baseline + at most 4 update (one per category) = 8 total.
