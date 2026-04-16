## Why

README 在初始版本后经历了大量功能迭代但没有同步更新。当前过时内容包括：
- 架构缺少 enrichment.py、dingtalk.py、_styles/ 目录
- formatter 接口签名过时（仍写 `set[str]`）
- 测试数量过时（写的 45，实际 68）
- 缺少 Issue 生命周期说明（聚合 + 自动关闭）
- 缺少 CodeBuddy Skills 使用说明（/formatter:add、/category:add 等）
- 缺少 enrichment（图文通知）特性说明
- 缺少开发者贡献指南（commit convention、git hooks）

## What Changes

- 重写 `README.md`（中文）
- 重写 `README_EN.md`（英文）

## Impact

- `README.md` — 重写
- `README_EN.md` — 重写
- 不涉及代码改动
