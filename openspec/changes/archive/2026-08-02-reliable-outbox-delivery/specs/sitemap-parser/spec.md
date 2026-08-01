## MODIFIED Requirements

### Requirement: Trusted content URLs
Only HTTPS URLs on `www.anthropic.com` SHALL enter monitored categories. Redirects followed during enrichment SHALL be validated before the next request.

#### Scenario: Untrusted sitemap host
- **WHEN** a sitemap entry is `http://127.0.0.1/news/internal`
- **THEN** it SHALL be excluded from all categories

### Requirement: Snapshot completeness guard
The system SHALL reject every sitemap snapshot unless all configured categories are non-empty and the combined monitored URL count is at least 300. Existing baselines SHALL never shrink.

#### Scenario: Grossly partial initial snapshot
- **WHEN** no baseline exists and the sitemap contains fewer than 300 monitored URLs or an empty configured category
- **THEN** processing SHALL fail before creating a baseline

#### Scenario: Existing URL disappears
- **WHEN** a valid snapshot no longer contains a previously known URL
- **THEN** the saved baseline SHALL retain that URL
