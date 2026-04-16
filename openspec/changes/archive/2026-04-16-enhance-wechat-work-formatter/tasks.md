## 1. Enrichment 模块

- [x] 1.1 写 `tests/test_enrichment.py`：抓取 og 元数据、fallback 到 slug、超时处理
- [x] 1.2 实现 `src/enrichment.py`：enrich_urls() 函数

## 2. Notifier 接口升级

- [x] 2.1 更新 `tests/test_notifier.py`：send_notifications 调用 enrich 后传递 enriched data
- [x] 2.2 修改 `src/notifier.py`：在 send_notifications 中调用 enrichment

## 3. WeChat Work Formatter 重写

- [x] 3.1 更新 `tests/formatters/test_wechat_work.py`：news 图文格式、enriched 输入
- [x] 3.2 重写 `src/formatters/wechat_work.py`：news 图文消息

## 4. DingTalk Formatter 适配

- [x] 4.1 更新 `tests/formatters/test_dingtalk.py`：适配 enriched 输入
- [x] 4.2 修改 `src/formatters/dingtalk.py`：使用 enriched title

## 5. Template 更新

- [x] 5.1 更新 `src/formatters/_template.py`：新接口文档
- [x] 5.2 更新 `tests/formatters/_template_test.py`：新接口示例

## 6. Documentation

- [x] 6.1 更新 `CODEBUDDY.md`：新增 enrichment 模块到架构

## 7. Verify

- [x] 7.1 运行全量测试确认通过

## 8. Ship

- [ ] 8.1 Commit, push, sync specs, archive
