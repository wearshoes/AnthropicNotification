# WeChat Work Message Styles

## A. 图文卡片 (news) — 当前使用

- **消息类型**: `news`
- **适合**: 视觉型用户，想看到封面图和标题
- **效果**:
  ```
  ┌──────────────────────────────────┐
  │ ┌────────┐                       │
  │ │ 封面图  │ Introducing Claude   │
  │ │        │ Opus 4.7             │
  │ └────────┘                       │
  │ Category: News                   │
  │ 点击查看详情 →                    │
  └──────────────────────────────────┘
  ```
- **限制**: 最多 8 篇 articles
- **payload 模板**:
  ```json
  {
    "msgtype": "news",
    "news": {
      "articles": [
        {
          "title": "{item.title}",
          "description": "{item.description or 'Category: ' + category}",
          "url": "{item.url}",
          "picurl": "{item.image or ''}"
        }
      ]
    }
  }
  ```

## B. 彩色 Markdown

- **消息类型**: `markdown`
- **适合**: 关注效率，快速扫一眼；支持 font color 高亮
- **效果**:
  ```
  ## Anthropic Website Update

  > 分类: (绿色)News
  > 新增: (橙色)1 篇

  **Introducing Claude Opus 4.7**
  [查看原文](https://...)
  (灰色)2026-04-16
  ```
- **限制**: 4096 字节；仅 3 种颜色 (info=绿, comment=灰, warning=橙)
- **payload 模板**:
  ```json
  {
    "msgtype": "markdown",
    "markdown": {
      "content": "## Anthropic Website Update\n\n> 分类: <font color=\"info\">{category}</font>\n> 新增: <font color=\"warning\">{count}</font> 篇\n\n**{item.title}**\n[查看原文]({item.url})\n<font color=\"comment\">{date}</font>"
    }
  }
  ```

## C. 结构化卡片 (template_card)

- **消息类型**: `template_card` (text_notice)
- **适合**: 运维/监控风格，结构化键值展示，有跳转按钮
- **效果**:
  ```
  ┌──────────────────────────────────┐
  │ 🔵 Anthropic Monitor      刚刚  │
  ├──────────────────────────────────┤
  │ ■ 网站内容更新                    │
  │                                  │
  │      1                           │
  │      篇新内容                     │
  │                                  │
  │ ─────────────────────            │
  │ 分类    News                     │
  │ 标题    Introducing Claude...    │
  │ 时间    2026-04-16               │
  │ ─────────────────────            │
  │                                  │
  │ [ 查看文章 ]       [ 全部 → ]    │
  └──────────────────────────────────┘
  ```
- **限制**: horizontal_content_list 最多 6 项; jump_list 最多 3 个
- **payload 模板**:
  ```json
  {
    "msgtype": "template_card",
    "template_card": {
      "card_type": "text_notice",
      "source": {"desc": "Anthropic Monitor"},
      "main_title": {"title": "Anthropic 网站内容更新", "desc": "发现 {count} 篇新内容"},
      "emphasis_content": {"title": "{count}", "desc": "篇新内容"},
      "horizontal_content_list": [
        {"keyname": "分类", "value": "{category}"},
        {"keyname": "标题", "value": "{item.title}"},
        {"keyname": "时间", "value": "{date}"}
      ],
      "jump_list": [{"type": 1, "title": "查看文章", "url": "{item.url}"}],
      "card_action": {"type": 1, "url": "{item.url}"}
    }
  }
  ```
