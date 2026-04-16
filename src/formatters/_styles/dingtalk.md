# DingTalk Message Styles

## A. Markdown 链接列表 — 当前使用

- **消息类型**: `markdown`
- **适合**: 简洁高效，列出标题和链接
- **效果**:
  ```
  ## Anthropic Website Update

  **News**:
  - [Introducing Claude Opus 4.7](https://...)
  - [Another Article](https://...)

  **Research**:
  - [New Paper](https://...)
  ```
- **限制**: 需要 title 字段（显示在通知栏）
- **payload 模板**:
  ```json
  {
    "msgtype": "markdown",
    "markdown": {
      "title": "Anthropic Website Update",
      "text": "## Anthropic Website Update\n\n**{category}**:\n- [{item.title}]({item.url})"
    }
  }
  ```
- **签名**: 可选 HMAC-SHA256 (`DINGTALK_SECRET`)

## B. Link 消息 (单条图文)

- **消息类型**: `link`
- **适合**: 单条更新时展示封面图 + 标题 + 描述
- **效果**:
  ```
  ┌──────────────────────────────────┐
  │ Introducing Claude Opus 4.7      │
  │                                  │
  │ Anthropic 发布了新内容...         │
  │                    ┌──────┐      │
  │                    │封面图│      │
  │                    └──────┘      │
  └──────────────────────────────────┘
  点击跳转原文
  ```
- **限制**: 每条消息只能展示 1 篇文章；多条更新时需发多条消息或改用 markdown
- **payload 模板**:
  ```json
  {
    "msgtype": "link",
    "link": {
      "title": "{item.title}",
      "text": "{item.description or 'Category: ' + category}",
      "picUrl": "{item.image or ''}",
      "messageUrl": "{item.url}"
    }
  }
  ```

## C. ActionCard (交互卡片)

- **消息类型**: `actionCard`
- **适合**: 多条更新，每条有独立跳转按钮
- **效果**:
  ```
  ┌──────────────────────────────────┐
  │ Anthropic Website Update          │
  │                                  │
  │ 发现 3 篇新内容:                  │
  │                                  │
  │ **News**: Introducing Claude...  │
  │ **Research**: New Paper on...    │
  │                                  │
  │ [ 查看 News ]  [ 查看 Research ] │
  └──────────────────────────────────┘
  ```
- **限制**: btnOrientation 0=竖排 1=横排; 横排最多 2 个按钮时效果好
- **payload 模板**:
  ```json
  {
    "msgtype": "actionCard",
    "actionCard": {
      "title": "Anthropic Website Update",
      "text": "## 发现 {count} 篇新内容\n\n**{category}**: {item.title}",
      "btnOrientation": "0",
      "btns": [
        {"title": "查看 {category}", "actionURL": "{item.url}"}
      ]
    }
  }
  ```
