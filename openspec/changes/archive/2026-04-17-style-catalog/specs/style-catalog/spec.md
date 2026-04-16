## ADDED Requirements

### Requirement: Style catalog per platform
Each supported platform SHALL have a style catalog file at `src/formatters/_styles/{platform}.md` listing available message styles with effect preview, payload template, limitations, and recommended use case.

#### Scenario: Platform has catalog
- **WHEN** `/formatter:add dingtalk` is invoked
- **AND** `src/formatters/_styles/dingtalk.md` exists
- **THEN** the skill SHALL present the predefined styles for user selection

#### Scenario: Platform has no catalog
- **WHEN** `/formatter:add custom_platform` is invoked
- **AND** no catalog file exists for that platform
- **THEN** the skill SHALL fall back to researching the platform API and designing styles from scratch

### Requirement: Custom style option
The skill SHALL always offer a "Custom" option alongside predefined styles. When chosen, the AI SHALL research the platform API, design a new style, and optionally push a preview to the user's webhook.

#### Scenario: User selects custom
- **WHEN** user selects "Custom" during style selection
- **THEN** the skill SHALL research the platform API and propose a new style
- **AND** offer to send a preview to the user's webhook for confirmation

### Requirement: Catalog self-evolution
After implementing a custom style, the skill SHALL ask the user if the new style should be saved to the platform's catalog for future use.

#### Scenario: User wants to save custom style
- **WHEN** user confirms saving the custom style
- **THEN** the skill SHALL append the new style to `src/formatters/_styles/{platform}.md`
