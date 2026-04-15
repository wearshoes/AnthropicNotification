## 1. CI Status Hook

- [x] 1.1 创建 `.codebuddy/hooks/ci-status.sh`：检测 git push，查询 Actions API
- [x] 1.2 更新 `.codebuddy/settings.json`：注册 ci-status hook

## 2. Verify

- [x] 2.1 测试 hook：模拟 git push 输入，验证输出
- [x] 2.2 运行全量测试确认无副作用
