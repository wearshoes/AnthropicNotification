## ADDED Requirements

### Requirement: DingTalk markdown message format
The dingtalk formatter SHALL produce a JSON payload with `msgtype: "markdown"` containing `title` and `text` fields.

#### Scenario: Format message with new URLs
- **WHEN** given changes with category `news` and URLs `[url_1, url_2]`
- **THEN** the payload SHALL have `msgtype` = `"markdown"`
- **AND** `markdown.title` SHALL contain a summary (e.g., "Anthropic Website Update")
- **AND** `markdown.text` SHALL list the URLs with category headers in markdown format

#### Scenario: Empty changes returns None
- **WHEN** given an empty changes dict
- **THEN** format_message SHALL return None

### Requirement: HMAC-SHA256 request signing
The dingtalk formatter SHALL sign requests using HMAC-SHA256 when `DINGTALK_SECRET` env var is set. The signature is computed as `HMAC-SHA256(timestamp + "\n" + secret)`, Base64 encoded, then URL encoded. Timestamp and sign are appended to the webhook URL as query parameters.

#### Scenario: Send with signing
- **WHEN** `DINGTALK_SECRET` env var is set
- **THEN** send SHALL append `&timestamp=<ms>&sign=<signature>` to the webhook URL
- **AND** the signature SHALL be computed as `URL_encode(Base64(HMAC-SHA256(timestamp + "\n" + secret)))`

#### Scenario: Send without signing
- **WHEN** `DINGTALK_SECRET` env var is NOT set
- **THEN** send SHALL POST to the webhook URL without timestamp/sign parameters

### Requirement: HTTP error handling
The dingtalk formatter SHALL raise on HTTP errors to allow the notifier to log and continue.

#### Scenario: HTTP error
- **WHEN** the webhook POST returns a non-2xx status
- **THEN** send SHALL raise an exception
