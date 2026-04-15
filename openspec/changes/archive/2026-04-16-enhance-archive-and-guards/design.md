## Context

项目已有 TDD guard hook 作为 PreToolUse 强约束的成功先例。现在扩展这种模式到 OpenSpec 流程保障和 commit 规范。

## Goals / Non-Goals

**Goals:**
- /opsx:archive 一键完成 sync + commit + push
- 被动提醒 agent 在修改代码前创建 OpenSpec change
- 强制 commit message 格式统一

**Non-Goals:**
- OpenSpec guard 不做硬阻断（用 ask 模式，保留紧急情况的灵活性）
- 不做 pre-push hook（过于侵入）

## Decisions

### 1. OpenSpec guard 使用 ask 模式而非 deny
deny 太强——紧急 hotfix 时会完全卡住。ask 模式弹确认，agent 可以选择先建 change 或强制继续。

### 2. Git commit-msg hook 放在 .githooks/ 目录
不放 .git/hooks/（不被 git 追踪），放 .githooks/ 并在 README 里说明需要 `git config core.hooksPath .githooks` 配置。GitHub Actions 里不需要（CI 不做 commit）。

### 3. Archive skill 的 git 操作
Archive skill 执行：sync specs → mv to archive → git add -A → git commit → git push。Commit message 使用固定模板 `chore: archive <name> change, sync specs`。

## Risks / Trade-offs

- [OpenSpec guard 假阳性] 如果 agent 修改模板文件或 __init__.py → hook 已排除 _ 前缀和 __init__.py
- [commit-msg hook 需要手动配置] 首次 clone 后需要执行 `git config core.hooksPath .githooks` → 在 README 里说明
