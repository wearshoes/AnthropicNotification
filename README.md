# Anthropic Notification

[English](README_EN.md) | 中文

监控 [Anthropic](https://www.anthropic.com) 网站内容更新，通过 Webhook 第一时间推送通知。

## 功能特性

- 基于 **Sitemap.xml** 检测内容更新，稳定可靠，不依赖页面 HTML 结构
- 使用 **GitHub Issues** 作为状态存储，无需数据库或外部服务
- 支持多平台 **Webhook 通知**（企业微信、钉钉、飞书、Slack、自定义）
- **页面元数据抓取**：自动获取文章标题、描述、封面图，通知更直观
- **GitHub Actions** 自动运行，每 30 分钟检查一次
- 约定式 **Formatter 发现机制**，新增通知平台只需添加一个文件
- **Issue 生命周期管理**：同分类只保留最新一个 update issue，旧的自动关闭
- 首次运行自动创建基线，不会产生通知轰炸

## 工作原理

```
                    ┌──────────────┐
                    │ Sitemap.xml  │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │ 按分类过滤    │  news / research / engineering / learn
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐     ┌──────────────┐
                    │ 对比基线      │◄────│ GitHub Issues│
                    │ (新 URL?)    │     │ (状态存储)    │
                    └──────┬───────┘     └──────────────┘
                           │
                    ┌──────▼───────┐
                    │ 发现新内容    │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
       创建聚合 Issue  更新基线    抓取元数据 + 发送通知
       (关闭旧的)     (追加URL)   (title/desc/image)
```

1. 通过 GitHub Actions 定时获取 `https://www.anthropic.com/sitemap.xml`
2. 将 URL 按路径前缀分为 4 个分类
3. 与 GitHub Issues 中存储的基线 URL 列表对比
4. 发现新 URL 后：
   - 创建一个聚合 Issue 记录所有新 URL，关闭该分类下的旧 update Issue
   - 抓取每个新页面的 title/description/image 元数据
   - 通过 Webhook 发送带封面图和标题的图文通知
5. 首次运行时静默创建基线（不发通知）

## 监控页面

| 分类 | URL 路径 | 内容类型 |
|------|----------|----------|
| news | `/news/*` | 产品发布、公司公告、政策声明 |
| research | `/research/*` | AI 安全研究论文、技术报告 |
| engineering | `/engineering/*` | 工程博客、技术实践 |
| learn | `/learn/*` | Anthropic Academy 课程 |

## 快速开始

### 第一步：Fork 仓库

点击本仓库右上角的 **Fork** 按钮，将仓库复制到你的 GitHub 账号下。

### 第二步：配置 Webhook Secret

1. 进入你 fork 后的仓库
2. 点击 **Settings** → **Secrets and variables** → **Actions**
3. 点击 **New repository secret**
4. 添加你需要的通知平台 Webhook：

| Secret 名称 | 说明 | 是否必须 |
|-------------|------|---------|
| `WECHAT_WORK_WEBHOOK` | 企业微信机器人 Webhook URL | 至少配一个 |
| `DINGTALK_WEBHOOK` | 钉钉自定义机器人 Webhook URL | 可选 |
| `DINGTALK_SECRET` | 钉钉机器人签名密钥 | 可选 |
| `FEISHU_WEBHOOK` | 飞书自定义机器人 Webhook URL | 可选 |
| `FEISHU_SECRET` | 飞书机器人签名密钥 | 可选 |
| `SLACK_WEBHOOK` | Slack Incoming Webhook URL | 可选 |
| `CUSTOM_WEBHOOK` | 任意自定义 Webhook 端点 | 可选 |

> 配置了哪个平台的 Webhook Secret，就会自动启用该平台的通知。不需要额外开关。

### 第三步：启用 GitHub Actions

1. 进入仓库的 **Actions** 标签页
2. 如果看到 "Workflows aren't being run on this forked repository"，点击 **I understand my workflows, go ahead and enable them**
3. 找到 **Monitor Anthropic Website** workflow
4. 点击 **Run workflow** → **Run workflow** 手动触发一次

### 第四步：验证

首次运行会：
- 在 Issues 中创建 4 个基线 Issue（[Baseline] news / research / engineering / learn）
- **不会发送通知**（这是预期行为，静默建立基线）

之后每 30 分钟自动检查一次。当 Anthropic 网站发布新内容时，你会：
- 收到带封面图和文章标题的图文通知
- 在 Issues 中看到一个聚合的 update Issue（同分类旧的自动关闭）

## 已支持的通知平台

| 平台 | Formatter | 消息格式 | 签名 |
|------|-----------|---------|------|
| 企业微信 | `wechat_work.py` | 图文卡片 (news) | 无 |
| 钉钉 | `dingtalk.py` | Markdown 链接列表 | HMAC-SHA256 (可选) |

## 添加新的通知平台

在 `src/formatters/` 目录下创建一个 Python 文件即可：

```
src/formatters/my_platform.py
```

文件需要导出两个函数：

```python
def format_message(changes: dict[str, list[dict]]) -> dict | None:
    """将变更格式化为平台特定的消息体。
    
    changes 格式: {"news": [{"url": "...", "title": "...", "description": "...", "image": "..."}]}
    """
    ...

def send(payload: dict, webhook_url: str) -> None:
    """发送消息到 Webhook。"""
    ...
```

然后在 GitHub Secrets 中添加 `MY_PLATFORM_WEBHOOK`。

系统会自动发现：文件名 `my_platform.py` → 对应环境变量 `MY_PLATFORM_WEBHOOK`。

参考 `src/formatters/_template.py` 了解完整的接口契约，参考 `src/formatters/_styles/` 目录下的消息风格 catalog 选择消息样式。

## 项目架构

```
src/
├── main.py              # 编排器：sitemap → detector → issues → notifier
├── sitemap.py           # 获取并解析 sitemap.xml，按分类过滤
├── detector.py          # 对比 sitemap URL 与基线，识别新内容
├── issues.py            # 通过 gh CLI 管理 GitHub Issues（基线 + 更新 + 自动关闭）
├── enrichment.py        # 抓取页面元数据（og:title, og:description, og:image）
├── notifier.py          # 约定式 formatter 发现 + 元数据丰富 + 分发通知
└── formatters/
    ├── _template.py     # Formatter 代码模板
    ├── _styles/         # 各平台消息风格 catalog
    │   ├── wechat_work.md
    │   ├── dingtalk.md
    │   ├── feishu.md
    │   └── slack.md
    ├── wechat_work.py   # 企业微信图文卡片格式化器
    └── dingtalk.py      # 钉钉 Markdown 格式化器（HMAC-SHA256 签名）

tests/                   # 单元测试（pytest, 68 个测试）
.github/workflows/
    └── monitor.yml      # GitHub Actions 工作流（每 30 分钟）
.githooks/
    └── commit-msg       # Git commit 消息格式校验
```

## CodeBuddy Skills

本项目集成了 [CodeBuddy Code](https://cnb.cool/codebuddy/codebuddy-code) 的 Skills 系统，提供自动化的开发流程：

| 命令 | 说明 |
|------|------|
| `/formatter:add <platform>` | 添加新通知平台，引导完整的 OpenSpec + TDD 流程，含消息风格选择 |
| `/category:add <name> <path>` | 添加新监控分类，引导更新代码 + 测试 + 文档 |
| `/opsx:explore` | 进入探索模式，用复利思维分析问题和方案 |
| `/opsx:propose` | 创建 OpenSpec 变更提案（proposal → specs → design → tasks） |
| `/opsx:apply` | 按 TDD 流程实现变更任务 |
| `/opsx:archive` | 归档变更，同步 specs，提交并推送 |

### 流程保障 Hooks

| Hook | 类型 | 作用 |
|------|------|------|
| `tdd-guard.sh` | PreToolUse | 写 src/ 前必须先有对应测试文件 |
| `tdd-autotest.sh` | PostToolUse | 写 src/ 后自动运行 pytest |
| `openspec-guard.sh` | PreToolUse | 修改 src/ 前提醒创建 OpenSpec 变更 |
| `ci-status.sh` | PostToolUse | git push 后自动查询 GitHub Actions 状态 |
| `commit-msg` | Git Hook | 校验 commit 消息格式 `<type>: <description>` |

## 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 配置 git hooks（commit 消息格式校验）
git config core.hooksPath .githooks

# 运行测试
python -m pytest tests/ -v

# 仅抓取 sitemap（不检测变更、不发通知）
python -m src.main --dry-run
```

### Commit 规范

```
<type>: <description>

type: feat | fix | docs | refactor | test | chore
```

## License

MIT
