# Anthropic Notification

[English](README_EN.md) | 中文

监控 [Anthropic](https://www.anthropic.com) 网站内容更新，通过 Webhook 第一时间推送通知。

## 功能特性

- 基于 **Sitemap.xml** 检测内容更新，稳定可靠，不依赖页面 HTML 结构
- 使用 **GitHub Issues** 作为状态存储，无需数据库或外部服务
- 支持多平台 **Webhook 通知**（企业微信、钉钉、飞书、Slack、自定义）
- **GitHub Actions** 自动运行，每 30 分钟检查一次
- 约定式 **Formatter 发现机制**，新增通知平台只需添加一个文件
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
                ┌──────────┼──────────┐
                ▼          ▼          ▼
         创建 Issue   更新基线    发送 Webhook
         (记录更新)   (追加URL)   (推送通知)
```

1. 通过 GitHub Actions 定时获取 `https://www.anthropic.com/sitemap.xml`
2. 将 URL 按路径前缀分为 4 个分类：news、research、engineering、learn
3. 与 GitHub Issues 中存储的基线 URL 列表对比
4. 发现新 URL 后：创建一个 Issue 记录 + 通过 Webhook 发送聚合通知
5. 首次运行时静默创建基线（不发通知，避免一次性推送几百条）

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
- 收到 Webhook 通知
- 在 Issues 中看到一个新的 update Issue

## 添加新的通知平台

在 `src/formatters/` 目录下创建一个 Python 文件即可：

```
src/formatters/my_platform.py
```

文件需要导出两个函数：

```python
def format_message(changes: dict[str, set[str]]) -> dict | None:
    """将变更格式化为平台特定的消息体。"""
    ...

def send(payload: dict, webhook_url: str) -> None:
    """发送消息到 Webhook。"""
    ...
```

然后在 GitHub Secrets 中添加 `MY_PLATFORM_WEBHOOK`。

系统会自动发现：文件名 `my_platform.py` → 对应环境变量 `MY_PLATFORM_WEBHOOK`。

## 项目架构

```
src/
├── main.py              # 编排器：sitemap → detector → issues → notifier
├── sitemap.py           # 获取并解析 sitemap.xml，按分类过滤
├── detector.py          # 对比 sitemap URL 与基线，识别新内容
├── issues.py            # 通过 gh CLI 管理 GitHub Issues（基线 + 更新）
├── notifier.py          # 约定式 formatter 发现 + 分发通知
└── formatters/
    └── wechat_work.py   # 企业微信 markdown 格式化器

tests/                   # 单元测试（pytest, 45 个测试）
.github/workflows/
    └── monitor.yml      # GitHub Actions 工作流（每 30 分钟）
```

## 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 运行测试
python -m pytest tests/ -v

# 仅抓取 sitemap（不检测变更、不发通知）
python -m src.main --dry-run
```

## License

MIT
