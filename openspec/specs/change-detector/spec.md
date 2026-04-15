## ADDED Requirements

### Requirement: Detect new URLs
The system SHALL compute the difference between current sitemap URLs and known baseline URLs per category. URLs present in sitemap but not in baseline are "new".

#### Scenario: New URLs exist
- **WHEN** sitemap has URLs {A, B, C} and baseline has {A, B}
- **THEN** the system SHALL report {C} as new

#### Scenario: No new URLs
- **WHEN** sitemap URLs and baseline URLs are identical
- **THEN** the system SHALL report an empty set

#### Scenario: First run (no baseline)
- **WHEN** no baseline exists for a category
- **THEN** the system SHALL treat all URLs as "initial" and NOT report them as new (silent baseline creation)
