## MODIFIED Requirements

### Requirement: Parse configured content sources
The system SHALL fetch both configured XML sitemaps and the exact `https://www.anthropic.com/engineering` landing page as one fail-closed snapshot.

#### Scenario: Engineering source fails
- **WHEN** fetching or parsing the engineering landing page fails
- **THEN** the run SHALL report failure
- **AND** previously pending delivery SHALL already have been attempted

### Requirement: Filter exclusive content categories
Trusted Anthropic news and research article URLs, engineering landing-page article URLs, and Claude Academy collection URLs SHALL be assigned to at most one category. Engineering landing-page membership SHALL override the generic research route. Category indexes, news section landing pages, research team pages, Academy lessons, and unrelated paths SHALL be excluded.

#### Scenario: Engineering article uses research path
- **WHEN** `/engineering` links to a sitemap URL under `/research/<slug>`
- **THEN** the URL SHALL be classified as engineering
- **AND** SHALL NOT also be classified as research

#### Scenario: Engineering link is not in sitemap
- **WHEN** `/engineering` links to a trusted article URL absent from the fetched sitemap
- **THEN** the URL SHALL be excluded from the snapshot

#### Scenario: News section landing page
- **WHEN** the sitemap contains a configured `/news/<section>` landing path
- **THEN** it SHALL NOT be classified as a news article
