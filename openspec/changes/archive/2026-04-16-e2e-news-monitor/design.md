## Context

全新项目，监控 Anthropic 网站更新。Anthropic 没有 RSS feed，但有标准 sitemap.xml（627 URLs，52KB，无需认证）。项目运行在 GitHub Actions 上，需要跨 run 持久化"已知 URL"状态。

## Goals / Non-Goals

**Goals:**
- 端到端跑通：sitemap 解析 → 变更检测 → Issue 创建 → 企业微信通知 → GitHub Actions 自动化
- 模块低耦合高内聚，formatter 支持约定式发现
- TDD 驱动开发

**Non-Goals:**
- 不做 HTML 内容解析（只用 sitemap 做 URL 级别的更新发现）
- 不做其他通知平台（钉钉/飞书/Slack/自定义 webhook 留到后续 change）
- 不做文章摘要提取或全文存储

## Decisions

### 1. Sitemap 作为唯一数据源，不做 HTML 解析

sitemap.xml 是 SEO 标准格式，比 HTML 结构稳定得多。虽然只能拿到 URL 和 lastmod，但项目目标是"发现更新"而非"抓取内容"。

**替代方案**: BeautifulSoup 解析各页面 HTML → 能拿到标题/分类/描述，但依赖 HTML 结构，网站改版即失效。

### 2. GitHub Issues 作为状态存储

每个监控分类一个 baseline Issue（始终 open），body 存该分类所有已知 URL。新发现的 URL 创建独立的 update Issue。

**替代方案**:
- git commit 状态文件 → 污染 git 历史，需要 contents:write 权限
- Actions Cache → 7 天过期，不可靠
- 外部存储 → 多一个依赖

### 3. 通过 `gh` CLI 操作 Issues，不用 GitHub REST API

GitHub Actions 预装 `gh`，且自动使用 `GITHUB_TOKEN` 认证。比手写 HTTP 请求更简洁可靠。

### 4. Formatter 约定式发现

`src/formatters/` 目录下的 `.py` 文件自动注册。文件名映射到环境变量：`wechat_work.py` → `WECHAT_WORK_WEBHOOK`。无需显式注册代码。

**替代方案**:
- 显式 import 注册 → 加平台要改两个文件
- 装饰器注册 → 对这个规模过度设计

### 5. 首次运行静默创建基线

首次运行某分类时，创建 baseline Issue 但不发通知，避免一次性推送几百条"新内容"。

### 6. `gh` CLI 调用方式

Python 中通过 `subprocess` 调用 `gh` 命令。虽然不如 REST API "纯粹"，但 `gh` 在 Actions 环境中开箱即用，认证零配置。

## Risks / Trade-offs

- [Sitemap 更新延迟] Anthropic 可能不实时更新 sitemap → 可接受，6 小时检测周期本身就不是实时的
- [Sitemap 格式变化] 虽然是标准格式但理论上可能变 → XML 解析比 HTML 解析稳定得多，风险很低
- [Issue body 大小] 500+ URL 约 30KB，GitHub Issue body 限制 65536 字符 → 足够，但需要监控
- [gh CLI 依赖] 本地开发需要安装 gh 并认证 → 测试中 mock subprocess 调用
- [Rate Limit] GitHub API 限制 5000 req/hour → 每次运行只需几个 API 调用，远低于限制

## Open Questions

（无，所有关键决策已在探索阶段确定）
