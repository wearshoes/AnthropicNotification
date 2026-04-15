## Why

首次部署到 GitHub Actions 后发现两个问题：
1. `gh issue create --label` 要求 label 预先存在，但新仓库没有任何 label，导致 issue 创建静默失败
2. `_run_gh()` 使用 `check=False`，命令失败时没有任何日志，问题难以排查

同时调整了运行频率从每 6 小时改为每 30 分钟，并添加了 push trigger 方便 workflow 文件变更时自动触发。

## What Changes

- `src/issues.py`: 添加 `_ensure_label()` 函数，在创建 issue 前自动创建缺失的 label（使用 `--force` 幂等）
- `src/issues.py`: `_run_gh()` 在命令失败时记录 ERROR 日志（stdout + stderr）
- `.github/workflows/monitor.yml`: cron 从 `0 */6 * * *` 改为 `*/30 * * * *`
- `.github/workflows/monitor.yml`: 添加 push trigger（限定 workflow 文件路径变更）

## Capabilities

### New Capabilities

（无新 capability）

### Modified Capabilities

- `issue-state`: 新增 label 自动创建和错误日志记录
- `ci-workflow`: 调整运行频率和触发条件

## Impact

- `src/issues.py` — 新增 `_ensure_label()` + logging
- `tests/test_issues.py` — 需要适配 label 创建的额外 gh 调用
- `.github/workflows/monitor.yml` — cron + push trigger
