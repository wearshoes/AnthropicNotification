## Why

添加新的监控分类（如 /blog, /customers）需要改 4 个地方：sitemap.py CATEGORIES、测试、两个 README、CODEBUDDY.md。这是与 formatter:add 类似的重复模式，适合封装成 skill。

## What Changes

- 新增 `.codebuddy/skills/category-add/SKILL.md`：封装监控分类添加流程
- 新增 `.codebuddy/commands/category/add.md`：`/category:add <name> <path>` 命令入口

## Capabilities

### New Capabilities
- `category-skill`: 自动化添加监控分类的 skill + command

### Modified Capabilities

（无）

## Impact

- `.codebuddy/skills/category-add/SKILL.md` — 新增
- `.codebuddy/commands/category/add.md` — 新增
- 不影响现有代码
