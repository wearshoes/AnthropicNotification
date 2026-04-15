## 1. OpenSpec Guard Hook

- [x] 1.1 创建 `.codebuddy/hooks/openspec-guard.sh`：检查活跃 change，ask 模式
- [x] 1.2 更新 `.codebuddy/settings.json`：注册 openspec-guard 到 PreToolUse

## 2. Git Commit Convention Hook

- [x] 2.1 创建 `.githooks/commit-msg`：校验 `<type>: <description>` 格式
- [x] 2.2 配置本地 git hooksPath 指向 `.githooks/`

## 3. Archive Skill 增强

- [x] 3.1 更新 `.codebuddy/skills/openspec-archive-change/SKILL.md`：加入 specs sync + commit + push
- [x] 3.2 更新 `.codebuddy/commands/opsx/archive.md`：同步更新

## 4. Documentation

- [x] 4.1 更新 `CODEBUDDY.md`：记录 commit convention、新 hooks、git hooksPath 配置

## 5. Verify

- [x] 5.1 测试 openspec-guard hook：有/无活跃 change 的行为
- [x] 5.2 测试 commit-msg hook：合法/非法格式
- [x] 5.3 运行全量测试确认无副作用
