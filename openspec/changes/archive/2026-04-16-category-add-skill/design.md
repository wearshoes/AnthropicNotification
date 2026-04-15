## Context

类似 formatter:add 的复利模式。sitemap.py 的 CATEGORIES 字典是添加分类的唯一代码入口。

## Goals / Non-Goals

**Goals:**
- 一条命令完成分类添加全流程
- 自动更新所有相关文件（代码、测试、文档）

**Non-Goals:**
- 不做动态分类发现（分类写死在代码里是设计决策）

## Decisions

### 1. Skill 引导修改现有文件而非创建新文件
添加分类不需要新模块，只需修改 sitemap.py + 测试 + 文档。Skill 指导 AI 找到正确位置插入。
