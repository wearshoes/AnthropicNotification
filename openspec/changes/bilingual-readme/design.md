## Context

README 是项目的门面，当前只有简略英文版。目标用户主要是中文开发者。

## Goals / Non-Goals

**Goals:**
- 中文 README 作为默认显示
- 包含完整的 fork→配置→运行教程
- 英文版作为备选

**Non-Goals:**
- 不做 i18n 框架，只是两个静态 markdown 文件
- 不做自动翻译

## Decisions

### 1. README.md 中文 + README_EN.md 英文
GitHub 默认显示 README.md，所以中文放在 README.md。顶部互相链接切换。

### 2. 内容结构
两个文件内容对等，结构一致：功能介绍 → 工作原理 → 快速开始(fork教程) → 配置说明 → 架构 → 扩展指南 → 本地开发
