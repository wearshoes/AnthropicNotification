## Why

每次 git push 后都要手动写一段 Python 脚本查询 GitHub Actions 状态，已重复多次。通过 PostToolUse hook 被动反馈，agent 自动获得 CI 状态。

## What Changes

- 新增 `.codebuddy/hooks/ci-status.sh`：git push 后自动查询 Actions 最新 run 状态
- 更新 `.codebuddy/settings.json`：注册 ci-status hook

## Capabilities

### New Capabilities
- `ci-status`: PostToolUse hook，push 后自动反馈 CI 状态

### Modified Capabilities

（无）

## Impact

- `.codebuddy/hooks/ci-status.sh` — 新增
- `.codebuddy/settings.json` — 注册新 hook
