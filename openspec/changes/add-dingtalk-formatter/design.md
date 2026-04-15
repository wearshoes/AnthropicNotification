## Context

钉钉自定义机器人 Webhook API。消息类型使用 markdown（有 title 和 text 两个字段）。安全机制使用加签模式（HMAC-SHA256）。限制 20 条/分钟。

## Goals / Non-Goals

**Goals:**
- 实现钉钉 markdown 消息通知
- 支持 HMAC-SHA256 签名（可选，有 secret 时启用）
- 遵循 formatter 接口契约

**Non-Goals:**
- 不做 @指定人 功能
- 不做 ActionCard 等其他消息类型

## Decisions

### 1. 使用 markdown 消息类型
钉钉支持 text/link/markdown/actionCard。markdown 最适合展示分类 + URL 列表，与企业微信格式一致。

### 2. 签名逻辑内置在 send() 中
签名通过 `os.environ.get("DINGTALK_SECRET")` 获取密钥。有密钥则签名，无密钥则直接发送。

## Risks / Trade-offs

- [Rate limit 20/min] 单次运行只发一条聚合消息，远低于限制
