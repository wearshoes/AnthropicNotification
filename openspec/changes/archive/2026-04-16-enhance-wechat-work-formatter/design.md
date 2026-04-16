## Context

企微消息从 markdown slug 列表升级为 news 图文卡片。需要 enrichment 层抓取页面元数据。

## Goals / Non-Goals

**Goals:**
- enrichment 层抓取 og:title/og:description/og:image
- 企微 formatter 改为 news 图文消息
- 所有 formatter 接口统一改为接收 enriched 数据
- 抓取失败优雅降级到 slug

**Non-Goals:**
- 不做全文抓取或 AI 摘要
- 不缓存抓取结果（每次运行重新抓取新 URL，量很小）

## Decisions

### 1. Enrichment 放在 notifier 层
notifier 在调用 formatter 前做一次 enrich，所有 formatter 共享数据。不在 formatter 里各自抓取（避免重复请求）。

### 2. Formatter 接口 breaking change
`changes` 从 `dict[str, set[str]]` 改为 `dict[str, list[dict]]`。这是一次性的接口升级，wechat_work、dingtalk、_template 一起改。

### 3. news 图文最多 8 条
企微 news 类型限制最多 8 篇 articles。超过 8 条时截断，因为单次运行发现 8+ 新 URL 的概率极低。

### 4. 抓取超时 5 秒
每个 URL 最多等 5 秒。GitHub Actions 有 6 小时超时，不会有问题。并发抓取可以后续优化。

## Risks / Trade-offs

- [网络请求增加] 每个新 URL 多一次 HTTP GET → 新 URL 通常 1-3 个，影响很小
- [og:description 可能是通用的] Anthropic 部分页面的 og:description 是公司简介而非文章摘要 → 可以判断是否通用，是则不显示
