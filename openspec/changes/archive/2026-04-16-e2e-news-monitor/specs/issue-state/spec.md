## ADDED Requirements

### Requirement: Read baseline Issue
The system SHALL find the open baseline Issue for a given category by searching for Issues with labels `baseline` and `<category>`. The Issue body contains one URL per line.

#### Scenario: Baseline Issue exists
- **WHEN** an open Issue with labels `baseline,news` exists
- **THEN** the system SHALL parse its body into a set of URL strings

#### Scenario: Baseline Issue does not exist
- **WHEN** no open Issue with labels `baseline,news` exists
- **THEN** the system SHALL return an empty set (first run for this category)

### Requirement: Create baseline Issue
The system SHALL create a new baseline Issue with labels `baseline` and `<category>`, with the body containing all known URLs (one per line).

#### Scenario: First run for a category
- **WHEN** no baseline Issue exists for category `news`
- **THEN** the system SHALL create one with title `[Baseline] news` and labels `baseline,news`
- **AND** the body SHALL contain all current URLs for that category

### Requirement: Update baseline Issue
The system SHALL append new URLs to the existing baseline Issue body.

#### Scenario: New URLs discovered
- **WHEN** 2 new URLs are found for category `news`
- **THEN** the system SHALL edit the baseline Issue body to include the new URLs
- **AND** the existing URLs in the body SHALL remain unchanged

### Requirement: Create update Issue
The system SHALL create a new Issue for each newly discovered URL with labels `<category>` and `update`.

#### Scenario: New article discovered
- **WHEN** a new URL `https://www.anthropic.com/news/new-article` is found
- **THEN** the system SHALL create an Issue with title derived from the URL slug
- **AND** labels SHALL be `news,update`
- **AND** the body SHALL contain the full URL and discovery timestamp
