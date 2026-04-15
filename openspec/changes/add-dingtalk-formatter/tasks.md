## 1. Tests

- [x] 1.1 写 `tests/formatters/test_dingtalk.py`：消息格式、签名算法、无签名降级、空 changes、HTTP 错误

## 2. Implementation

- [x] 2.1 实现 `src/formatters/dingtalk.py`：markdown 格式化 + HMAC-SHA256 签名发送

## 3. Workflow

- [x] 3.1 在 `.github/workflows/monitor.yml` 添加 DINGTALK_WEBHOOK 和 DINGTALK_SECRET env（已预置）

## 4. Verify

- [x] 4.1 运行全量测试确认通过
