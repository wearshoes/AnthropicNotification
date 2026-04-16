# Feishu (Lark) Message Styles

## A. 富文本 (post)

- **消息类型**: `post`
- **适合**: 简洁通知，支持链接、加粗、标签
- **效果**:
  ```
  Anthropic Website Update

  News:
  · Introducing Claude Opus 4.7  [查看]
  · Another Article              [查看]
  
  Research:
  · New Paper Title              [查看]
  ```
- **限制**: 不支持图片内嵌；链接通过 tag 实现
- **payload 模板**:
  ```json
  {
    "msg_type": "post",
    "content": {
      "post": {
        "zh_cn": {
          "title": "Anthropic Website Update",
          "content": [
            [
              {"tag": "text", "text": "{category}: "},
              {"tag": "a", "text": "{item.title}", "href": "{item.url}"}
            ]
          ]
        }
      }
    }
  }
  ```
- **签名**: 可选 HMAC-SHA256 (`FEISHU_SECRET`)

## B. 交互卡片 (interactive)

- **消息类型**: `interactive`
- **适合**: 视觉丰富，支持多栏布局、按钮、分割线
- **效果**:
  ```
  ┌──────────────────────────────────┐
  │ Anthropic Website Update          │
  │ 发现 2 篇新内容                    │
  ├──────────────────────────────────┤
  │                                  │
  │ 📰 News                          │
  │ Introducing Claude Opus 4.7      │
  │ Our latest model with improved   │
  │ reasoning capabilities.          │
  │ [ 查看原文 ]                      │
  │                                  │
  │ ─────────────────                │
  │                                  │
  │ 🔬 Research                       │
  │ New Paper Title                  │
  │ [ 查看原文 ]                      │
  │                                  │
  └──────────────────────────────────┘
  ```
- **限制**: 卡片 JSON 结构较复杂；需要构建 elements 数组
- **payload 模板**:
  ```json
  {
    "msg_type": "interactive",
    "card": {
      "header": {
        "title": {"tag": "plain_text", "content": "Anthropic Website Update"},
        "template": "blue"
      },
      "elements": [
        {"tag": "div", "text": {"tag": "lark_md", "content": "**{category}**\n{item.title}"}},
        {"tag": "action", "actions": [
          {"tag": "button", "text": {"tag": "plain_text", "content": "查看原文"}, "url": "{item.url}", "type": "primary"}
        ]},
        {"tag": "hr"}
      ]
    }
  }
  ```

## C. 纯文本 (text)

- **消息类型**: `text`
- **适合**: 最简模式，纯通知
- **效果**:
  ```
  [Anthropic Update] News: Introducing Claude Opus 4.7
  https://www.anthropic.com/news/claude-opus-4-7
  ```
- **限制**: 无格式；适合极简场景
- **payload 模板**:
  ```json
  {
    "msg_type": "text",
    "content": {
      "text": "[Anthropic Update] {category}: {item.title}\n{item.url}"
    }
  }
  ```
