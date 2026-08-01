# Anthropic Notification

[English](README_EN.md) | 中文

监控 [Anthropic](https://www.anthropic.com) 发布的新内容，并通过企业微信或钉钉 Webhook 推送通知。

## 功能特性

- 基于 Sitemap 监控 news、research、engineering、learn 四类内容
- 使用 GitHub Issues 保存持久化基线和通知 outbox
- 至少一次投递：按消息块记录回执，失败后自动重试
- 完整分块：企业微信每条最多 8 篇，多出的内容继续发送，不再截断丢失
- 批次超出 GitHub Issue 正文限制时，自动拆分为多个 outbox 事件
- 自动抓取页面标题、描述和封面图
- GitHub 状态与 Webhook 操作均采用故障关闭策略
- GitHub Actions 单写者串行执行，并设置运行超时
- 首次运行静默创建基线，不发送历史内容

## 可靠性模型

发现新 URL 后按以下顺序处理：

1. 校验并规范化 sitemap 快照。
2. 抓取新页面元数据，把固定的目标、目的地指纹、formatter 版本、分块成员和 payload 持久化到一个或多个大小受限的 outbox Issue。
3. 重新读取 Issue，确认持久化成功。
4. 用 `已知 URL ∪ 当前 URL` 扩展基线。
5. 逐个发送 pending 消息块，每次成功后立即保存回执。
6. 所有目标消息块都有回执后，将 Issue 标记为 delivered。

Webhook 平台不提供可用的幂等键。如果进程在平台已接收消息、但回执尚未保存时停止，该消息块可能在下次运行时重复发送。因此系统保证的是持久化的**至少一次投递**，不是恰好一次。GitHub API 故障、目标凭证缺失、formatter 版本不匹配、HTTP 错误或平台返回非零 `errcode` 时，任务保持 pending 并让工作流失败。

workflow 每 30 分钟请求调度一次，但 GitHub Actions 的定时任务是尽力执行，可能被 GitHub 延迟或跳过。需要立即检查时可使用 `workflow_dispatch` 手动触发。

## 监控页面

| 分类 | URL 路径 | 内容类型 |
|------|----------|----------|
| news | `/news/*` | 产品发布、公司公告 |
| research | `/research/*` | AI 安全论文、技术报告 |
| engineering | `/engineering/*` | 工程博客 |
| learn | `/learn/*` | Anthropic Academy 课程 |

系统只接受精确位于 `https://www.anthropic.com` 的规范 URL。四个分类必须都非空且内容总数不少于 300，否则拒绝该快照；已有基线不会缩小。

## 快速开始

1. Fork 本仓库。
2. 在 **Settings → Secrets and variables → Actions** 中至少配置一个已实现平台：

| Secret | 说明 | 是否必须 |
|--------|------|----------|
| `WECHAT_WORK_WEBHOOK` | 企业微信机器人 Webhook URL | 至少一个目标 |
| `DINGTALK_WEBHOOK` | 钉钉自定义机器人 Webhook URL | 至少一个目标 |
| `DINGTALK_SECRET` | 钉钉签名密钥 | 可选 |

3. 在 fork 中启用 GitHub Actions。
4. 手动运行一次 **Monitor Anthropic Website**。

首次成功运行会为四个分类各创建一个 baseline Issue，并且不会发送通知。后续发现新内容时会创建机器可读的 update Issue。若出现新内容时没有启用任何 formatter，任务会失败且基线不会推进。

## 已支持平台

| 平台 | Formatter | 消息格式 | 签名 |
|------|-----------|----------|------|
| 企业微信 | `wechat_work.py` | 图文卡片，每块最多 8 篇 | 无 |
| 钉钉 | `dingtalk.py` | Markdown 链接，每块最多 20 项 | 可选 HMAC-SHA256 |

本仓库目前没有实现飞书、Slack 和自定义 Webhook。

## 添加平台

创建 `src/formatters/my_platform.py`：

```python
FORMATTER_VERSION = 1
MAX_ITEMS_PER_MESSAGE = 10

def format_message(changes: dict[str, list[dict]]) -> dict | None:
    ...

def send(payload: dict, webhook_url: str) -> None:
    ...
```

`send()` 只有在 HTTP 与平台业务状态都成功时才能返回，否则必须抛出异常。随后需要同时在 GitHub Secrets 和 `.github/workflows/monitor.yml` 的 `Run monitor` 环境变量中加入 `MY_PLATFORM_WEBHOOK`。已存在的 pending 事件会继续使用创建时保存的目标、目的地指纹、契约版本、分块与 payload；若目标 URL 改变，旧 pending 投递会被阻止，而不会被静默转发到新地址。

完整契约见 `src/formatters/_template.py`。

## 项目架构

```text
src/
├── main.py              # 恢复 pending、接收快照、完成事件
├── sitemap.py           # 可信抓取、URL 规范化、分类
├── detector.py          # 快照保护、差异检测、持久化顺序
├── outbox.py            # 稳定 ID、不可变分块、回执
├── issues.py            # 写后验证的 GitHub Issue 状态操作
├── enrichment.py        # 带重定向校验的页面元数据抓取
├── notifier.py          # Formatter 发现、规划与分块投递
├── webhook_http.py      # 重试与平台业务响应校验
└── formatters/
    ├── _template.py
    ├── wechat_work.py
    └── dingtalk.py
```

## 本地开发

完整的非 dry-run 执行需要 Python 3.11+ 和 GitHub CLI (`gh`)。

```bash
pip install -r requirements.txt
git config core.hooksPath .githooks
python -m pytest tests -v
python -m src.main --dry-run
```

Commit 使用 `<type>: <description>` 格式，type 可选 `feat`、`fix`、`docs`、`refactor`、`test`、`chore`。

## License

MIT
