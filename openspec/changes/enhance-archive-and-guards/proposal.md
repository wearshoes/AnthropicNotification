## Why

三个重复出现的流程问题：
1. `/opsx:archive` 每次都要手动 sync specs + commit + push，已重复 5 次
2. 修改 src/ 时可能忘了先创建 OpenSpec change（之前 hotfix 就踩过坑）
3. Commit 消息格式不统一，没有强制规范

这三个问题都可以通过被动约束机制解决，一次投入，永久生效。

## What Changes

- 增强 `/opsx:archive` skill：自动 sync specs + git commit + git push
- 新增 `.codebuddy/hooks/openspec-guard.sh`：修改 src/ 前检查是否有活跃的 OpenSpec change（软约束，ask 模式）
- 新增 `.githooks/commit-msg`：校验 commit message 格式 `<type>: <description>`
- 更新 `.codebuddy/settings.json`：注册 openspec-guard hook
- 更新 `CODEBUDDY.md`：记录 commit convention 和新 hooks

## Capabilities

### New Capabilities
- `openspec-guard`: PreToolUse hook，修改 src/ 前检查 OpenSpec change 状态
- `commit-convention`: Git commit-msg hook，强制 commit 消息格式

### Modified Capabilities
- `ci-workflow`: /opsx:archive skill 增强

## Impact

- `.codebuddy/skills/openspec-archive-change/SKILL.md` — 增强
- `.codebuddy/commands/opsx/archive.md` — 同步增强
- `.codebuddy/hooks/openspec-guard.sh` — 新增
- `.codebuddy/settings.json` — 注册新 hook
- `.githooks/commit-msg` — 新增
- `CODEBUDDY.md` — 更新 conventions
