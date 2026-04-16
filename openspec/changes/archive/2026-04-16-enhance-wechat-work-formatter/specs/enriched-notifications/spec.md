## ADDED Requirements

### Requirement: Page metadata enrichment
The system SHALL fetch each new URL's page and extract og:title, og:description, and og:image metadata. If fetching fails, the system SHALL fall back to slug-based title with no description/image.

#### Scenario: Page has og metadata
- **WHEN** the system fetches `https://www.anthropic.com/news/claude-opus-4-7`
- **AND** the page contains `<meta property="og:title" content="Introducing Claude Opus 4.7"/>`
- **THEN** the enriched data SHALL include `title: "Introducing Claude Opus 4.7"`

#### Scenario: Page fetch fails
- **WHEN** the system cannot fetch a URL (timeout, 404, etc.)
- **THEN** the enriched data SHALL fall back to `title: "claude-opus-4-7"` (slug from URL)
- **AND** description and image SHALL be None

## MODIFIED Requirements

### Requirement: Formatter interface change
All formatters SHALL accept `changes: dict[str, list[dict]]` where each dict contains `url`, `title`, `description`, and `image` fields.

#### Scenario: Formatter receives enriched data
- **WHEN** format_message is called
- **THEN** changes SHALL be `{"news": [{"url": "...", "title": "...", "description": "...", "image": "..."}]}`

### Requirement: WeChat Work news format
The wechat_work formatter SHALL produce `msgtype: "news"` with articles containing title, description, url, and picurl fields.

#### Scenario: Single new article
- **WHEN** 1 new URL is found with title "Introducing Claude Opus 4.7"
- **THEN** the payload SHALL be `{"msgtype": "news", "news": {"articles": [{...}]}}`
- **AND** the article SHALL have title, description, url, and picurl

#### Scenario: Multiple new articles (max 8)
- **WHEN** 10 new URLs are found
- **THEN** the payload SHALL include the first 8 articles (news type limit)

#### Scenario: No image available
- **WHEN** an article has no og:image
- **THEN** the article's picurl SHALL be omitted or empty
