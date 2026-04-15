## Context

首次部署后发现 `gh issue create --label` 在 label 不存在时静默失败。根本原因是 `_run_gh` 使用 `check=False` 且没有日志，导致失败不可见。

## Goals / Non-Goals

**Goals:**
- 修复 label 不存在时 issue 创建失败的问题
- 添加 gh CLI 调用的错误日志
- 调整运行频率为 30 分钟

**Non-Goals:**
- 不改变 issue 的整体存储架构
- 不改变 formatter 发现机制

## Decisions

### 1. 使用 `gh label create --force` 自动创建 label
`--force` 使其幂等——label 存在时不报错。使用模块级 `_ensured_labels` 集合缓存已创建的 label，同一次运行内不重复调用。

### 2. 在 `_run_gh` 中统一添加错误日志
任何 gh 命令失败时，记录完整的 command、stdout、stderr。不改变返回行为（仍然不 raise），让调用方决定如何处理。

## Risks / Trade-offs

- [Label 创建额外 API 调用] 每次运行首次遇到每个 label 时多一次 gh 调用 → 通过缓存最小化，每个 label 只创建一次
- [30 分钟频率] GitHub Actions 免费额度为 2000 分钟/月，每次运行约 30 秒，每天 48 次 = 月消耗约 720 分钟 → 在免费额度内
