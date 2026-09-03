## MODIFIED Requirements

### Requirement: Parse configured sitemap XML sources
The system SHALL fetch both `https://www.anthropic.com/sitemap.xml` and `https://academy.claude.com/sitemap.xml` and combine the `loc` and optional `lastmod` entries into one snapshot.

#### Scenario: One configured source fails
- **WHEN** fetching or parsing either configured sitemap fails
- **THEN** the run SHALL report failure
- **AND** previously pending delivery SHALL already have been attempted

### Requirement: Trusted canonical content URLs
Only category routes on the exact `https://www.anthropic.com` and `https://academy.claude.com` origins SHALL enter monitored categories. Query strings and fragments SHALL be removed from item identity. Every redirect target followed during sitemap or metadata fetches SHALL be validated before the next request.

#### Scenario: Academy lookalike host
- **WHEN** an entry uses `https://academy.claude.com.evil.test/collections/a`
- **THEN** it SHALL be excluded from every category

### Requirement: Filter categories
Trusted Anthropic URLs SHALL be grouped by `/news/`, `/research/`, and `/engineering/`. Trusted Claude Academy URLs under `/collections/` SHALL be grouped as `learn`. Category index pages, legacy `/learn/*` paths, Academy lessons, and unrelated paths SHALL be excluded.

#### Scenario: Academy course lesson
- **WHEN** an Academy URL uses the `/courses/` prefix
- **THEN** it SHALL NOT be classified as a learn collection
