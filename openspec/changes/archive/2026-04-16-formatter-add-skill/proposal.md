## Why

每次新增通知平台 formatter 都需要重复相同的流程：创建文件、写测试、实现接口、更新 workflow、走 OpenSpec 流程。这个流程高度模式化，适合封装成 skill，实现"一条命令完成一个 formatter 全生命周期"。

## What Changes

- 新增 `.codebuddy/skills/formatter-add/SKILL.md`：封装 formatter 开发的完整流程指令
- 新增 `.codebuddy/commands/formatter/add.md`：`/formatter:add <platform>` 命令入口
- 新增 `src/formatters/_template.py`：formatter 代码模板，供 skill 参考
- 新增 `tests/formatters/_template_test.py`：测试模板，供 skill 生成测试骨架

## Capabilities

### New Capabilities
- `formatter-skill`: 自动化 formatter 开发流程的 skill + command，含代码模板和测试模板

### Modified Capabilities

（无）

## Impact

- `.codebuddy/skills/formatter-add/SKILL.md` — 新增 skill
- `.codebuddy/commands/formatter/add.md` — 新增命令
- `src/formatters/_template.py` — 代码参考模板
- `tests/formatters/_template_test.py` — 测试参考模板
- 不影响现有代码，不需要修改已有测试
