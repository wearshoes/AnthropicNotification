## ADDED Requirements

### Requirement: Parse sitemap XML
The system SHALL fetch `https://www.anthropic.com/sitemap.xml` and parse all `<url>` entries, extracting `<loc>` and `<lastmod>` fields.

#### Scenario: Successful sitemap fetch
- **WHEN** the system fetches the sitemap
- **THEN** it SHALL return a list of URL entries, each containing `loc` (string) and `lastmod` (string or None)

#### Scenario: Network error
- **WHEN** the sitemap fetch fails (timeout, DNS, HTTP error)
- **THEN** the system SHALL raise an exception with a descriptive error message

### Requirement: Filter URLs by category
The system SHALL classify URLs into categories based on path prefix: `/news/*`, `/research/*`, `/engineering/*`, `/learn/*`. URLs not matching any category SHALL be ignored.

#### Scenario: URL matches a known category
- **WHEN** a URL has path prefix `/news/some-article`
- **THEN** it SHALL be classified under category `news`

#### Scenario: URL does not match any category
- **WHEN** a URL is `https://www.anthropic.com/careers`
- **THEN** it SHALL be excluded from the results

#### Scenario: Category grouping
- **WHEN** the sitemap contains URLs across multiple categories
- **THEN** the output SHALL be a dict mapping category name to a set of URL strings
