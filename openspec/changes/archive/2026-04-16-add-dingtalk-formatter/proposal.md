## Why

扩展通知平台覆盖。钉钉是国内主流企业协作工具，添加钉钉 formatter 让更多用户能接收 Anthropic 网站更新通知。这是 `/formatter:add` skill 的首次实战验证。

## What Changes

- 新增 `src/formatters/dingtalk.py`：钉钉 markdown 消息格式化 + HMAC-SHA256 签名发送
- 新增 `tests/formatters/test_dingtalk.py`：完整单元测试
- 更新 `.github/workflows/monitor.yml`：添加 DINGTALK_WEBHOOK 和 DINGTALK_SECRET 环境变量

## Capabilities

### New Capabilities
- `dingtalk-formatter`: 钉钉自定义机器人 Webhook 通知，支持 markdown 消息和加签安全

### Modified Capabilities

（无）

## Impact

- `src/formatters/dingtalk.py` — 新增
- `tests/formatters/test_dingtalk.py` — 新增
- `.github/workflows/monitor.yml` — 添加 2 行 env
