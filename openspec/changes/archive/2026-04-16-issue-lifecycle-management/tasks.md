## 1. Tests — issues.py

- [x] 1.1 更新 `tests/test_issues.py`：`create_update_issue` 改为接受 URL 集合，测试聚合 title/body
- [x] 1.2 新增 `tests/test_issues.py`：`close_old_update_issues` 测试关闭旧 issues、跳过 baseline

## 2. Implementation — issues.py

- [x] 2.1 修改 `src/issues.py`：`create_update_issue(category, urls: set[str])`，聚合 body
- [x] 2.2 新增 `src/issues.py`：`close_old_update_issues(category)`

## 3. Tests — detector.py

- [x] 3.1 更新 `tests/test_detector.py`：`process_category` 调用 `create_update_issue` 一次传所有 URL + 调用 close

## 4. Implementation — detector.py

- [x] 4.1 修改 `src/detector.py`：一次调用 `create_update_issue(category, new_urls)` + `close_old_update_issues(category)`

## 5. Verify

- [x] 5.1 运行全量测试确认通过
