## Requirements

### Requirement: Parse configured content sources
The system SHALL fetch both configured XML sitemaps and the exact `https://www.anthropic.com/engineering` landing page as one fail-closed snapshot. Sitemap entries SHALL contribute `loc` and optional `lastmod` values. The engineering page SHALL contribute trusted article membership.

#### Scenario: One configured source fails
- **WHEN** fetching or parsing either configured sitemap or the engineering landing page fails
- **THEN** the run SHALL report failure
- **AND** previously pending delivery SHALL already have been attempted

### Requirement: Trusted canonical content URLs
Only category routes on the exact `https://www.anthropic.com` and `https://academy.claude.com` origins SHALL enter monitored categories. Query strings and fragments SHALL be removed from item identity. Every redirect target followed during sitemap or metadata fetches SHALL be validated before the next request.

#### Scenario: Lookalike host
- **WHEN** an entry uses `https://www.anthropic.com.evil.test/news/a`
- **THEN** it SHALL be excluded from every category

#### Scenario: Unconfigured-origin redirect
- **WHEN** a content page redirects to an origin outside the exact trusted set
- **THEN** the unconfigured origin SHALL NOT be requested

### Requirement: Filter exclusive content categories
Trusted Anthropic news and research article URLs, engineering landing-page article URLs, and Claude Academy collection URLs SHALL be assigned to at most one category. Engineering landing-page membership SHALL override the generic research route. Category indexes, news section landing pages, research team pages, Academy lessons, and unrelated paths SHALL be excluded. Direct `/engineering/<slug>` sitemap entries SHALL remain supported.

#### Scenario: Category index
- **WHEN** a URL path is exactly `/news`
- **THEN** it SHALL NOT be classified as an article

#### Scenario: Academy course lesson
- **WHEN** an Academy URL uses the `/courses/` prefix
- **THEN** it SHALL NOT be classified as a learn collection

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

### Requirement: Snapshot completeness guard
The system SHALL reject every sitemap snapshot unless all configured categories are non-empty and the combined monitored URL count is at least 300. Existing baselines SHALL never shrink.

#### Scenario: Grossly partial initial snapshot
- **WHEN** no baseline exists and the sitemap contains fewer than 300 monitored URLs or an empty configured category
- **THEN** processing SHALL fail before creating a baseline

#### Scenario: Existing URL disappears
- **WHEN** a valid snapshot no longer contains a previously known URL
- **THEN** the saved baseline SHALL retain that URL
