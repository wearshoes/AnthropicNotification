## Context

刚才企微消息美化的过程验证了"先看效果再决定"的价值。把这个模式固化到 skill 里。

## Goals / Non-Goals

**Goals:**
- 每个已知平台提供 2-3 个预设风格（含效果预览 + payload 模板）
- 自定义出口：AI 实时研究 + 预览推送
- 好的自定义方案可以沉淀回 catalog

**Non-Goals:**
- 不做 GUI 预览工具
- catalog 不需要覆盖所有消息类型，只收录适合通知场景的

## Decisions

### 1. Catalog 文件放在 `src/formatters/_styles/`
以 `_` 开头的目录不会被 notifier 扫描。每个平台一个 .md 文件。

### 2. 每个 style 的标准结构
名称、消息类型、适合场景、效果预览（ASCII 示意）、payload JSON 模板、限制说明。AI 读了就能实现。

### 3. 已有平台的 catalog 现在就写
wechat_work 和 dingtalk 已实现，把它们的可选风格补全。再加 feishu 和 slack 的预设。
