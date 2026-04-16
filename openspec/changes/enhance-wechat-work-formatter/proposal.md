## Why

企微推送消息过于简陋——只有 slug 链接列表，没有文章标题、封面图、描述。改用图文消息（news 类型）后，消息有封面图 + 标题 + 描述 + 点击跳转，用户体验大幅提升。

同时需要一个 enrichment 层来抓取页面元数据（title、og:image、og:description），这个层放在 notifier 中，所有 formatter 共享。

## What Changes

- 新增 `src/enrichment.py`：抓取页面 og:title、og:description、og:image 元数据
- 修改 `src/notifier.py`：分发前调用 enrichment 丰富 URL 数据
- 修改 `src/formatters/wechat_work.py`：从 markdown 改为 news 图文消息类型
- 修改 formatter 接口：`changes` 从 `dict[str, set[str]]` 变为 `dict[str, list[dict]]`
- 同步更新 `src/formatters/dingtalk.py`、`src/formatters/_template.py`
- 更新所有相关测试

## Capabilities

### New Capabilities
- `enrichment`: 页面元数据抓取层，提取 title/description/image

### Modified Capabilities
- `webhook-notifier`: 分发前 enrich URLs，formatter 接收丰富数据
- `wechat-work-formatter`: 从 markdown 改为 news 图文卡片

## Impact

- `src/enrichment.py` — 新增
- `src/notifier.py` — 修改 send_notifications 流程
- `src/formatters/wechat_work.py` — 重写为 news 类型
- `src/formatters/dingtalk.py` — 适配新接口
- `src/formatters/_template.py` — 更新接口文档
- `tests/` — 全部相关测试更新
