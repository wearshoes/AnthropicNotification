## Why

监控 Anthropic 网站内容更新，第一时间通过 Webhook 获知新发布的文章、研究论文、工程博客等内容。当前没有 RSS 订阅源可用，需要主动检测变更。

## What Changes

- 新增 sitemap.xml 解析模块，从 Anthropic 网站获取全量 URL 列表
- 新增 GitHub Issues 作为状态存储，用基线 Issue 记录已知 URL，用 update Issue 记录新发现的内容
- 新增企业微信 Webhook 通知，将新内容聚合为一条消息推送
- 新增 GitHub Actions 工作流，每 6 小时自动运行检测
- 使用约定式发现机制加载 formatter，便于后续扩展通知平台

## Capabilities

### New Capabilities
- `sitemap-parser`: 获取并解析 Anthropic sitemap.xml，按分类（news/research/engineering/learn）过滤和分组 URL
- `issue-state`: 通过 GitHub Issues 管理状态——创建/读取/更新基线 Issue，创建 update Issue 记录新内容
- `change-detector`: 对比 sitemap URL 与基线 Issue 中的已知 URL，识别新增内容
- `webhook-notifier`: 将新发现的内容通过 Webhook 发送通知，支持约定式 formatter 发现机制，首个实现为企业微信
- `ci-workflow`: GitHub Actions 定时工作流，编排完整的检测→通知流程

### Modified Capabilities

（无，这是全新项目）

## Impact

- 新增 Python 模块: `src/sitemap.py`, `src/issues.py`, `src/notifier.py`, `src/formatters/wechat_work.py`, `src/main.py`
- 新增 GitHub Actions workflow: `.github/workflows/monitor.yml`
- 依赖: `requests`, `beautifulsoup4`/`lxml`(解析 XML), GitHub CLI (`gh`)
- 权限: `GITHUB_TOKEN` 需要 `issues:write`
- Secrets: `WECHAT_WORK_WEBHOOK`（企业微信 Webhook URL）
