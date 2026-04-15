## ADDED Requirements

### Requirement: Discover formatters by convention
The system SHALL scan the `src/formatters/` directory and load formatter modules. A file named `<platform>.py` that exports `format_message(category, urls)` and `send(payload, webhook_url)` SHALL be registered as a formatter for `<platform>`. Files starting with `_` or named `__init__.py` SHALL be skipped.

#### Scenario: Formatter file exists with matching env var
- **WHEN** `src/formatters/wechat_work.py` exists
- **AND** environment variable `WECHAT_WORK_WEBHOOK` is set
- **THEN** the system SHALL load and use this formatter

#### Scenario: Formatter file exists but no env var
- **WHEN** `src/formatters/wechat_work.py` exists
- **AND** environment variable `WECHAT_WORK_WEBHOOK` is NOT set
- **THEN** the system SHALL skip this formatter

#### Scenario: Explicitly disabled
- **WHEN** environment variable `WECHAT_WORK_ENABLED` is set to `false`
- **THEN** the system SHALL skip this formatter regardless of webhook URL presence

### Requirement: Send aggregated notification
The system SHALL aggregate all new URLs discovered in a single run into one notification message per enabled platform.

#### Scenario: Multiple categories have updates
- **WHEN** news has 2 new URLs and research has 1 new URL
- **THEN** the system SHALL send one message per platform containing all 3 updates grouped by category

#### Scenario: Notification failure does not block others
- **WHEN** sending to platform A fails
- **THEN** the system SHALL log the error and continue sending to platform B

### Requirement: WeChat Work message format
The wechat_work formatter SHALL produce a markdown message compatible with WeChat Work webhook API (`msgtype: "markdown"`).

#### Scenario: Format message with new URLs
- **WHEN** given category `news` with URLs `[url_1, url_2]`
- **THEN** the payload SHALL be a JSON dict with `msgtype: "markdown"` and a `markdown.content` field listing the URLs with category header

#### Scenario: Message size limit
- **WHEN** the formatted message exceeds 4096 bytes
- **THEN** the system SHALL truncate the URL list and append a summary count
