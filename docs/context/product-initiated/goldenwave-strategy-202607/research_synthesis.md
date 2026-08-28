---
req_id: goldenwave-strategy-202607
type: research-synthesis
status: active
updated: 2026-07-24
source_root: /Users/goldenwave/KnowledgeBase
---

# GoldenWave 战略研究摘要

## 研究范围

本摘要记录 2026-07-24 对个人知识库的定向检索结果，用于支持 GoldenWave 产品战略。它只保留与产品判断有关的低敏结论，不复制 Profile 私密正文。

## 主要证据

| 来源页面 | 页面更新时间 | 可支持的最小结论 |
|---|---:|---|
| `wiki/projects/goldenwave开源项目.md` | 2026-06-30 | GoldenWave 已形成五层 SPEC、Skill 与本地 Markdown/Git 起点，但仍以骨架为主 |
| `wiki/concepts/个人操作系统五层架构.md` | 2026-06-30 | Profile、Knowledge、Workflow、Project、Git 可作为职责分离的信息模型 |
| `wiki/methods/个人Profile事实档案系统.md` | 2026-06-30 | 当前事实需要与可复用知识分离，并携带敏感度、来源和核验周期 |
| `wiki/methods/Profile与AI工作流数据治理协议.md` | 2026-06-30 | Profile 的读写、核验、隐私和回流需要显式协议 |
| `wiki/syntheses/个人Agent协作Harness.md` | 2026-06-30 | 用户已在个人知识库、多个项目仓库和多个 Agent 间形成真实协作环境 |
| `wiki/concepts/AI团队知识分层架构.md` | 2026-07-19 | 工作流会变化，跨项目验证后的知识更可能形成长期复利 |
| `wiki/concepts/Agent-Loop治理层.md` | 2026-06-16 | 自动化 Loop 需要独立治理以降低失忆、误写和重复失败 |
| `wiki/methods/Agent经验自进化闭环.md` | 2026-07-22 | 运行 Trace 需清洗、验证并形成候选经验，不能直接污染正式知识 |
| `wiki/syntheses/Agent-Skills自进化与编排.md` | 2026-07-22 | Skill 自进化需要 Candidate、Eval Gate、版本、来源和回滚 |
| `wiki/insights/OpenHuman个人Agent操作系统竞品观察.md` | 2026-06-30 | 完整个人 Agent OS 验证了需求叙事，但托管后端和黑盒记忆与本项目原则冲突 |
| `wiki/insights/Pieces个人AI记忆层竞品观察.md` | 2026-06-30 | 被动捕获与时间记忆有市场证据，但结构化沉淀和治理可作为其下游互补层 |
| `wiki/methods/多Agent时代Skill管理方案.md` | 2026-06-24 | 多 Agent 环境存在 Skill 版本碎片、来源和冲突治理问题 |

## 已观察事实与推论边界

### 已观察

- 个人 KnowledgeBase 存在 `profile/`、`wiki/`、分级索引和治理脚本；
- 用户的个人 Harness 同时涉及 Claude Code、Codex、Hermes、项目仓库与 Git；
- GoldenWave 仓库已包含 SPEC、五层分册、初始化脚本和四个 Skill 骨架；
- 当前仓库尚无统一 CLI、Context Pack、Candidate Validator 或跨 Agent 评测报告。

### 战略推论，尚待验证

- 用户是否愿意为“可信治理”承担 Candidate review 成本；
- 同一 Context Pack 能否显著提升不同 Agent 的一致性；
- Markdown 默认实现能否覆盖目标用户的数据规模；
- 个人知识分类中哪些部分能成为公共 Contract；
- 受治理经验是否能稳定改善后续任务质量或成本。

## 结论

个人知识库支持把 GoldenWave 定位为“可信个人上下文治理层”，但不能证明该产品已经具备治理闭环或跨 Agent 复利。应先把现有个人体系用作 dogfooding 证据场，再通过指标协议、威胁模型、两个外部设计伙伴和阶段 Gate 决定哪些能力可以成为公共标准。

## 知识缺口

- 缺少外部用户访谈和行为数据；
- 缺少同任务在不同 Agent、不同上下文策略下的对照结果；
- 缺少 Candidate 审阅成本和接受率数据；
- 缺少开源同类产品的可重复基准，而非仅定性观察；
- 缺少本地存储在大规模数据下的性能与恢复测试。
