## 1. Sitemap Parser

- [x] 1.1 写 `tests/test_sitemap.py` 单元测试：解析 XML、按分类过滤、网络错误处理
- [x] 1.2 实现 `src/sitemap.py`：fetch_sitemap() + filter_by_category()，使测试通过

## 2. Issue State Manager

- [x] 2.1 写 `tests/test_issues.py` 单元测试：读取基线 Issue、创建基线 Issue、更新基线 Issue、创建 update Issue（mock gh CLI 调用）
- [x] 2.2 实现 `src/issues.py`：通过 subprocess 调用 gh CLI 管理 Issues，使测试通过

## 3. Change Detector

- [x] 3.1 写 `tests/test_detector.py` 单元测试：新 URL 检测、无变化、首次运行静默基线
- [x] 3.2 实现 `src/detector.py`：对比 sitemap URL 与基线 URL，识别新增内容，使测试通过

## 4. Webhook Notifier + WeChat Work Formatter

- [x] 4.1 写 `tests/test_notifier.py` 单元测试：formatter 发现机制、聚合通知、单平台失败不阻塞
- [x] 4.2 写 `tests/formatters/test_wechat_work.py` 单元测试：消息格式、大小截断
- [x] 4.3 实现 `src/notifier.py`：约定式扫描 formatters/ 目录、匹配环境变量、分发通知，使测试通过
- [x] 4.4 实现 `src/formatters/wechat_work.py`：企业微信 markdown 消息格式化 + 发送，使测试通过

## 5. Main Orchestrator

- [x] 5.1 写 `tests/test_main.py` 单元测试：完整流程编排（mock sitemap/issues/notifier）
- [x] 5.2 实现 `src/main.py`：串联 sitemap → detector → issues → notifier 完整流程，使测试通过

## 6. GitHub Actions Workflow

- [x] 6.1 创建 `.github/workflows/monitor.yml`：cron 每 6 小时、workflow_dispatch、注入 secrets、权限配置

## 7. 端到端验证

- [x] 7.1 本地运行全量测试 `python -m pytest tests/ -v` 确认全部通过
- [x] 7.2 本地手动运行 `python -m src.main --dry-run` 验证 sitemap 能正常获取和解析
