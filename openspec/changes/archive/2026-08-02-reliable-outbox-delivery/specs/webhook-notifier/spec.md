## MODIFIED Requirements

### Requirement: Complete planned delivery
Each formatter SHALL plan one or more immutable payload chunks that collectively cover every item assigned to that formatter. The dispatcher SHALL surface failures after attempting independent targets.

#### Scenario: Sixteen WeChat Work items
- **WHEN** an event contains 16 items for WeChat Work
- **THEN** the plan SHALL contain two payloads of at most 8 articles
- **AND** every item SHALL occur in exactly one payload

### Requirement: Platform response validation
Formatters SHALL treat non-2xx responses, redirects, invalid JSON, and platform business error responses as delivery failures. Credential-bearing URLs and untrusted remote error text SHALL NOT appear in surfaced errors. Only bounded integer business error codes MAY appear; all other returned error-code values SHALL be represented as `unknown`.

#### Scenario: HTTP 200 business error
- **WHEN** WeChat Work returns HTTP 200 with a non-zero `errcode`
- **THEN** the chunk SHALL remain pending
- **AND** the workflow SHALL report failure

#### Scenario: Webhook redirect
- **WHEN** a webhook responds with a redirect to another URL
- **THEN** the redirect SHALL NOT be followed
- **AND** the chunk SHALL remain pending

#### Scenario: Untrusted error-code value
- **WHEN** a webhook returns a URL, string, boolean, or oversized integer as `errcode`
- **THEN** surfaced errors SHALL show `errcode=unknown`
- **AND** SHALL NOT expose the returned value
