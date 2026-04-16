## Why

Update Issues 永远不会关闭，长期运行后会无限累积。需要 Issue 生命周期管理：基线永不关闭，每个 category 只保留最新一个 open 的 update issue，旧的自动关闭。同时将同一次运行发现的多个新 URL 聚合为一个 issue。

## What Changes

- 修改 `src/issues.py`：新增 `close_old_update_issues()` 关闭旧 update issues，修改 `create_update_issue()` 改为接受多个 URL 聚合成一个 issue
- 修改 `src/detector.py`：从"每个 URL 一个 issue"改为"每个 category 一个聚合 issue"
- 更新测试

## Capabilities

### Modified Capabilities
- `issue-state`: update issue 创建改为聚合模式 + 旧 issue 自动关闭

## Impact

- `src/issues.py` — 修改 `create_update_issue()`，新增 `close_old_update_issues()`
- `src/detector.py` — 修改 `process_category()` 调用方式
- `tests/test_issues.py` — 更新测试
- `tests/test_detector.py` — 更新测试
