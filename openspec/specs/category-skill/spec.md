## ADDED Requirements

### Requirement: Skill 封装分类添加全流程
`/category:add <name> <path>` SHALL guide the AI through: OpenSpec propose → TDD (update sitemap.py CATEGORIES + tests) → update READMEs → update CODEBUDDY.md → commit → archive.

#### Scenario: Add a new category
- **WHEN** user invokes `/category:add blog /blog/`
- **THEN** the skill SHALL create an OpenSpec change, update CATEGORIES dict, update tests, update docs, and commit

#### Scenario: Derive names from input
- **WHEN** user provides name `blog` and path `/blog/`
- **THEN** the skill SHALL add `"blog": "/blog/"` to CATEGORIES and update all references
