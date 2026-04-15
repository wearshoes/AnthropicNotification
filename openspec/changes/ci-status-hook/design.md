## Context

之前每次 push 后都手动用 Python urllib 查 Actions API。这可以自动化为 PostToolUse hook。

## Goals / Non-Goals

**Goals:**
- Push 后被动获得 CI 状态反馈
- 尽力而为（有 token 就查，没有就跳过）

**Non-Goals:**
- 不做 CI 失败自动修复
- 不等 CI 完成（只查当前状态，不轮询到结束）

## Decisions

### 1. 用 Python 而非 curl 查 API
本地环境 curl 有网络问题，Python urllib 更可靠（之前验证过）。

### 2. 检测 git push 用字符串匹配
从 hook 输入的 `tool_input.command` 中检查是否包含 `git push`。简单可靠。

### 3. 查最新 1 个 run 而非等待完成
只查 status/conclusion，不等 in_progress 变 completed。返回当前快照即可，agent 按需再查。
