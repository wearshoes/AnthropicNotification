## Requirements

### Requirement: Parse sitemap XML
The system SHALL fetch `https://www.anthropic.com/sitemap.xml` and extract the `loc` and optional `lastmod` of each URL entry.

#### Scenario: Network failure
- **WHEN** fetching or parsing the sitemap fails
- **THEN** the run SHALL report failure
- **AND** previously pending delivery SHALL already have been attempted

### Requirement: Trusted canonical content URLs
Only URLs on the exact `https://www.anthropic.com` origin SHALL enter monitored categories. Query strings and fragments SHALL be removed from item identity. Every redirect target followed during sitemap or metadata fetches SHALL be validated before the next request.

#### Scenario: Lookalike host
- **WHEN** an entry uses `https://www.anthropic.com.evil.test/news/a`
- **THEN** it SHALL be excluded from every category

#### Scenario: Cross-origin redirect
- **WHEN** an Anthropic page redirects to another origin
- **THEN** the other origin SHALL NOT be requested

### Requirement: Filter categories
Trusted URLs SHALL be grouped by `/news/`, `/research/`, `/engineering/`, and `/learn/` path prefix. Category index pages and unrelated paths SHALL be excluded.

#### Scenario: Category index
- **WHEN** a URL path is exactly `/news`
- **THEN** it SHALL NOT be classified as an article

### Requirement: Snapshot completeness guard
The system SHALL reject every sitemap snapshot unless all configured categories are non-empty and the combined monitored URL count is at least 300. Existing baselines SHALL never shrink.

#### Scenario: Grossly partial initial snapshot
- **WHEN** no baseline exists and the sitemap contains fewer than 300 monitored URLs or an empty configured category
- **THEN** processing SHALL fail before creating a baseline

#### Scenario: Existing URL disappears
- **WHEN** a valid snapshot no longer contains a previously known URL
- **THEN** the saved baseline SHALL retain that URL
