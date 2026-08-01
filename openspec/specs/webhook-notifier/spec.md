## Requirements

### Requirement: Discover implemented formatters by convention
The system SHALL load non-underscore modules in `src/formatters/` only when their `<PLATFORM>_WEBHOOK` environment variable is configured and the formatter is not explicitly disabled.

#### Scenario: Missing webhook credential
- **WHEN** a formatter module exists but its webhook environment variable is absent
- **THEN** that formatter SHALL NOT be included as a new-event target

### Requirement: Block new content without targets
When new content exists and no formatter is enabled, the system SHALL fail before creating an outbox event or advancing the baseline.

#### Scenario: No formatter enabled
- **WHEN** a non-initial run detects a new URL and no target is configured
- **THEN** the baseline SHALL remain unchanged
- **AND** the workflow SHALL fail

### Requirement: Complete planned delivery
Each formatter SHALL plan one or more immutable payload chunks that collectively cover every assigned item exactly once. Failures SHALL be surfaced after independent targets have been attempted.

#### Scenario: Sixteen WeChat Work items
- **WHEN** an event contains 16 WeChat Work items
- **THEN** the plan SHALL contain two payloads with at most 8 articles each
- **AND** every item SHALL occur in exactly one payload

### Requirement: Platform response validation
Formatters SHALL retry bounded delivery attempts and treat non-2xx responses, redirects, invalid JSON, and non-zero platform business error codes as failures. Credential-bearing URLs and untrusted remote error text SHALL NOT appear in surfaced errors. Only bounded integer business error codes MAY appear; all other returned error-code values SHALL be represented as `unknown`.

#### Scenario: HTTP 200 business error
- **WHEN** WeChat Work returns HTTP 200 with non-zero `errcode`
- **THEN** the chunk SHALL remain pending
- **AND** the workflow SHALL fail

#### Scenario: Webhook redirect
- **WHEN** a webhook responds with a redirect to another URL
- **THEN** the redirect SHALL NOT be followed
- **AND** the chunk SHALL remain pending

#### Scenario: Untrusted error-code value
- **WHEN** a webhook returns a URL, string, boolean, or oversized integer as `errcode`
- **THEN** surfaced errors SHALL show `errcode=unknown`
- **AND** SHALL NOT expose the returned value
