## ADDED Requirements

### Requirement: Skill 封装 formatter 开发全流程
`/formatter:add <platform>` SHALL guide the AI through the complete formatter development lifecycle: OpenSpec propose → TDD (RED → GREEN) → workflow update → test → commit → archive.

#### Scenario: Add a new formatter
- **WHEN** user invokes `/formatter:add dingtalk`
- **THEN** the skill SHALL create an OpenSpec change, generate test skeleton, implement the formatter following TDD, update workflow env, run tests, and commit

#### Scenario: Platform name validation
- **WHEN** user provides a platform name
- **THEN** the skill SHALL derive file paths (`src/formatters/{name}.py`, `tests/formatters/test_{name}.py`) and env var name (`{NAME}_WEBHOOK`) from the platform name

### Requirement: 代码模板
`src/formatters/_template.py` SHALL serve as a reference template showing the formatter interface contract: `format_message(changes)` and `send(payload, webhook_url)`.

#### Scenario: AI reads template before implementing
- **WHEN** the skill starts implementing a new formatter
- **THEN** it SHALL read `_template.py` to understand the interface contract and message formatting patterns

### Requirement: 测试模板
`tests/formatters/_template_test.py` SHALL serve as a reference template showing standard test patterns for formatters.

#### Scenario: AI generates tests from template
- **WHEN** the skill enters TDD RED phase
- **THEN** it SHALL reference `_template_test.py` to generate platform-specific tests covering: format single/multiple categories, empty changes, size truncation, send POST, send error handling
