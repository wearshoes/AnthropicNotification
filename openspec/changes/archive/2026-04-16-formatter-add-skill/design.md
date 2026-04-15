## Context

项目已有 wechat_work formatter 作为参考实现，约定式发现机制已就位。新增 formatter 的流程完全模式化。

## Goals / Non-Goals

**Goals:**
- Skill 内嵌完整流程：OpenSpec → TDD → workflow → commit
- 代码模板和测试模板降低 AI 的认知负担
- 让平台特定知识（消息格式、签名算法）成为唯一需要 AI 研究的部分

**Non-Goals:**
- 不做代码生成器/脚手架工具（skill 是给 AI 的指令，不是 CLI 工具）
- 模板只作参考，不做 cookiecutter 式的变量替换

## Decisions

### 1. 模板用 `_` 前缀命名
`_template.py` 和 `_template_test.py` 以下划线开头，`notifier.py` 的 discover 逻辑已经跳过 `_` 开头的文件，所以模板不会被当成 formatter 加载。

### 2. Skill 引导 AI 查阅平台 API 文档
Skill 不内嵌各平台的 API 细节（会过时），而是指导 AI 用 WebFetch/WebSearch 查阅最新文档。

### 3. Skill 集成 OpenSpec 和 TDD 流程
一条命令触发完整链路，而不是让用户手动走 `/opsx:propose` → `/opsx:apply` → `/opsx:archive`。

## Risks / Trade-offs

- [模板过时] 如果 formatter 接口变了，模板需要同步更新 → 接口极简（2 个函数），变化概率低
- [Skill 指令过长] 完整流程步骤多，skill 文件较大 → 可接受，skill 只在调用时加载
