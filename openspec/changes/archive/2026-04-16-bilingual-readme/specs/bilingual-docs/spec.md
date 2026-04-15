## ADDED Requirements

### Requirement: 中文 README 作为默认
README.md SHALL be written in Chinese as the default language, with a language switch link at the top pointing to README_EN.md.

#### Scenario: User opens repository
- **WHEN** a user visits the repository on GitHub
- **THEN** they SHALL see the Chinese README by default
- **AND** a link at the top SHALL allow switching to English

### Requirement: 英文 README 作为备选
README_EN.md SHALL contain the English version of the README, with a language switch link back to README.md.

#### Scenario: User switches to English
- **WHEN** a user clicks the English link in README.md
- **THEN** they SHALL be directed to README_EN.md with equivalent content

### Requirement: 功能介绍
Both README files SHALL include a clear description of what the project does: monitor Anthropic website via sitemap, detect new content, send webhook notifications, use GitHub Issues as state storage.

#### Scenario: New user reads README
- **WHEN** a new user reads the README
- **THEN** they SHALL understand the project's purpose, monitoring mechanism, and notification flow

### Requirement: Fork 配置教程
Both README files SHALL include step-by-step instructions for forking and configuring the project: fork, configure Secrets, enable Actions, verify.

#### Scenario: User follows fork tutorial
- **WHEN** a user follows the fork tutorial
- **THEN** they SHALL be able to set up their own monitoring instance with their own webhook URLs

### Requirement: 架构说明
Both README files SHALL include the project file structure and module responsibilities.

#### Scenario: Developer reads architecture
- **WHEN** a developer wants to extend the project
- **THEN** they SHALL understand which file does what
