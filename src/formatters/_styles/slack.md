# Slack Message Styles

## A. Block Kit 富消息

- **消息类型**: `blocks`
- **适合**: 结构化展示，有分割线、链接按钮、上下文信息
- **效果**:
  ```
  ┌──────────────────────────────────┐
  │ Anthropic Website Update          │
  ├──────────────────────────────────┤
  │                                  │
  │ *News*                           │
  │ *Introducing Claude Opus 4.7*    │
  │ Our latest model with improved   │
  │ reasoning capabilities.          │
  │ 📎 <View Article>                │
  │                                  │
  │ ─────────────────                │
  │                                  │
  │ *Research*                       │
  │ *New Paper Title*                │
  │ 📎 <View Article>                │
  │                                  │
  │ 🕐 Detected at 2026-04-16       │
  └──────────────────────────────────┘
  ```
- **限制**: blocks 数组最多 50 个; 单个 text block 最多 3000 字符
- **payload 模板**:
  ```json
  {
    "blocks": [
      {"type": "header", "text": {"type": "plain_text", "text": "Anthropic Website Update"}},
      {"type": "divider"},
      {"type": "section", "text": {"type": "mrkdwn", "text": "*{category}*\n*{item.title}*\n{item.description or ''}"}, "accessory": {"type": "button", "text": {"type": "plain_text", "text": "View"}, "url": "{item.url}"}},
      {"type": "divider"},
      {"type": "context", "elements": [{"type": "mrkdwn", "text": "Detected at {date}"}]}
    ]
  }
  ```

## B. Mrkdwn 简洁文本

- **消息类型**: `text` (with mrkdwn)
- **适合**: 简洁快速，像 Markdown 但用 Slack 语法
- **效果**:
  ```
  *Anthropic Website Update*

  *News:*
  • <https://...|Introducing Claude Opus 4.7>
  
  *Research:*
  • <https://...|New Paper Title>
  ```
- **限制**: 不支持图片内嵌; mrkdwn 语法与标准 Markdown 不同 (`*bold*` 而非 `**bold**`)
- **payload 模板**:
  ```json
  {
    "text": "*Anthropic Website Update*\n\n*{category}:*\n• <{item.url}|{item.title}>"
  }
  ```

## C. Attachment 卡片 (legacy 但仍可用)

- **消息类型**: `attachments`
- **适合**: 带颜色条和字段的卡片样式
- **效果**:
  ```
  ┌──────────────────────────────────┐
  │▌Anthropic Website Update          │
  │▌                                  │
  │▌ News                             │
  │▌ Introducing Claude Opus 4.7     │
  │▌ Our latest model with improved  │
  │▌ reasoning capabilities.         │
  │▌                                  │
  │▌ Category: News  |  2026-04-16   │
  └──────────────────────────────────┘
  (左侧有蓝色竖条)
  ```
- **限制**: Slack 官方建议迁移到 Block Kit; 但 attachments 仍然可用且更简单
- **payload 模板**:
  ```json
  {
    "attachments": [
      {
        "color": "#2196F3",
        "title": "{item.title}",
        "title_link": "{item.url}",
        "text": "{item.description or ''}",
        "fields": [
          {"title": "Category", "value": "{category}", "short": true},
          {"title": "Detected", "value": "{date}", "short": true}
        ],
        "thumb_url": "{item.image or ''}"
      }
    ]
  }
  ```
