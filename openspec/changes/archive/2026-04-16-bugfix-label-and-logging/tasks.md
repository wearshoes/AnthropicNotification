## 1. Issue State — Label 自动创建 + Error Logging

- [x] 1.1 写/更新 `tests/test_issues.py`：测试 _ensure_label 调用、error logging、label 缓存
- [x] 1.2 实现 `src/issues.py`：_ensure_label() + _run_gh() error logging，使测试通过

## 2. CI Workflow

- [x] 2.1 修改 `.github/workflows/monitor.yml`：cron 改为 30 分钟 + 添加 push trigger

## 3. 验证

- [x] 3.1 补充 _ensure_label 的专项测试：缓存机制、幂等性
- [x] 3.2 补充 _run_gh error logging 的测试
- [x] 3.3 运行全量测试确认通过
