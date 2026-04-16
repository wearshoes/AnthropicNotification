## Why

`/formatter:add` skill 在实现 formatter 时缺少"消息风格选择"步骤。开发者需要自己研究平台 API 来决定消息格式。通过 style catalog，预设各平台的可选消息风格（含效果预览和 payload 模板），让开发者直接选择。同时保留自定义出口——自定义的好方案可以沉淀回 catalog，形成自我进化的资产。

## What Changes

- 新增 `src/formatters/_styles/` 目录，含各平台的 style catalog 文件
- 更新 `.codebuddy/skills/formatter-add/SKILL.md`：加入 style 选择步骤 + 自定义出口
- 更新 `CODEBUDDY.md`：文档说明

## Capabilities

### New Capabilities
- `style-catalog`: 各平台预设消息风格 catalog，含效果预览和 payload 模板

### Modified Capabilities
- `formatter-skill`: 加入 style 选择步骤

## Impact

- `src/formatters/_styles/*.md` — 新增
- `.codebuddy/skills/formatter-add/SKILL.md` — 更新
- `CODEBUDDY.md` — 更新
- 不涉及代码改动，不需要 TDD
