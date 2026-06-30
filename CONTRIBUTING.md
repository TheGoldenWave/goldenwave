# Contributing to goldenwave

goldenwave 是一个**开放标准 + Skill 套件**，欢迎共建。

## 如何贡献
- **完善 SPEC**：对 L1–L5 分层规范提 issue / PR。
- **新增 Skill**：在 `skills/` 下按现有 `SKILL.md` 风格新增，挂任意 agent 可用。
- **贡献模板**：`templates/` 下的页面模板、frontmatter schema。
- **适配新 agent**：让 Skill 在更多 agent（Cursor / Codex / Windsurf...）上可用。

## 原则
1. 任何改动不得破坏"设计红线"（见 ROADMAP.md）。
2. 新增字段 / 页面类型，先更新 SPEC，再改实现。
3. 一切产物保持纯 markdown，可被 git diff。

## 协议
贡献即同意以 [MIT](LICENSE) 授权。注：v0.2+ 若复用第三方 GNU 组件（如 immortal 采集器），相关子目录单独标注其许可。
