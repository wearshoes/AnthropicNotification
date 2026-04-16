## Context

当前 `create_update_issue()` 每个 URL 创建一个 issue，且从不关闭。需要改为聚合 + 自动关闭。

## Goals / Non-Goals

**Goals:**
- 同一次运行同一 category 的新 URL 聚合成一个 issue
- 创建新 update issue 后关闭同 category 的旧 update issues
- 稳态 open issues <= 8

**Non-Goals:**
- 不关闭 baseline issues
- 不做跨 category 聚合（每个 category 独立）

## Decisions

### 1. `create_update_issue()` 改为接受 `set[str]` 而非单个 URL
函数签名从 `create_update_issue(category, url)` 改为 `create_update_issue(category, urls)`。单个 URL 时 title 用 slug，多个时用 `N new updates`。

### 2. `close_old_update_issues()` 用 gh issue close
查找同 category 的 open update issues（labels: `{category},update`），逐个 close。在创建新 issue 之后执行——确保新的已存在再关旧的。

### 3. detector.py 从循环调用改为一次调用
`process_category()` 里从 `for url in new_urls: create_update_issue(category, url)` 改为 `create_update_issue(category, new_urls)`。

## Risks / Trade-offs

- [gh issue close API 调用] 每个旧 issue 一次 close 调用 → 正常情况下每 category 最多关 1 个（上次的）
- [首次清理] 现有 #5 和 #6 都是 open，下次运行时如果有新 news URL，会关闭它们
