---
snapshot_schema: source-snapshot/v1
source_id: src_execution_board
original_path: docs/prd/goldenwave-strategy/.artifacts/execution-board.md
original_content_sha256: 9dbee6f17df9e20bc7694ed1c35aff48e2de97dac03c5eeb4e3327d81706305e
observed_at: '2026-07-25'
sanitization: Repository low-sensitivity document snapshot; contains no L3 or private body text.
---
---
feature_id: goldenwave-strategy
stage: phase-0
status: active
updated: 2026-07-24
accountable: primary-agent
responsible_for_status: project-manager-agent
---

# GoldenWave 执行看板

## 当前里程碑

- **Phase**：0 — Strategy & Baseline
- **状态**：Yellow（战略已完成，执行基线尚未建立）
- **目标**：冻结可信内核的风险边界和验收 Oracle，为 Phase 1 提供可测试输入。
- **用户参与预算**：Phase 0 最多 1 个边界决策包、1 次外部引荐请求、1 次 Gate 确认。

## 状态枚举

`backlog / todo / in_progress / review / waiting_external / blocked / done`

## Phase 0

| ID | 工作项 | Responsible | Status | Depends On | Evidence ID | Needs User Decision |
|---|---|---|---|---|---|---|
| P0-01 | 协作章程与单一看板 | primary | done | - | E-P0-01 | no |
| P0-02 | 核验入口文档 `RTK.md` 外层引用 | primary | done | P0-01 | E-P0-02 | no |
| P0-03 | KnowledgeBase 结构、Agent 接入与存储等级盘点 | primary | done | P0-01 | E-P0-03 | no |
| P0-04 | Threat Model 与权限矩阵 | architect | done | P0-03 | E-P0-04 | no-current-d2 |
| P0-05a | 20 个 contract/security 任务与 120 断言 | qa | done | P0-03 | E-P0-05a | no |
| P0-05b | 20 个真实 dogfood 任务与可重放 Oracle | qa | review | P0-03/P0-04 | E-P0-05b | representative-only |
| P0-06 | 人工代理流程基线 | qa + primary | todo | P0-05b | E-P0-06 | no |
| P0-07 | 设计伙伴协议与访谈材料 | pm | todo | P0-04/P0-05b | E-P0-07 | no |
| P0-08 | 设计伙伴名单、知情同意、引荐与访谈 | pm | todo | P0-07 | E-P0-08 | introduction-only |
| P0-09 | Phase 0 Gate Review | primary + independent reviewers | todo | P0-02..08 | E-P0-09 | go-no-go |

### P0-03 盘点边界

现有用户授权已覆盖读取 `/Users/goldenwave/KnowledgeBase` 以支持 GoldenWave 规划。盘点默认只读取结构、索引、Schema、低敏 Profile 控制台和 Agent 接入配置：

- 不读取 `profile/` 中 L3 正文、`.private/`、财务、健康、亲友原始信息；
- 不复制个人正文到项目仓库；
- 输出仅含数量、类型、路径类别、风险和脱敏示例；
- 遇到无法从元数据判断的敏感文件，标记 unknown，不为完成盘点而展开正文。

### Phase 0 Gate

- 定位、边界和红线无冲突；
- Threat Model 通过非作者评审；
- 20 个任务覆盖 Profile / Knowledge / Project，且 >=100 条断言可复核；
- 人工基线保留原始记录；
- 两名设计伙伴已知情同意并确认核心问题存在；
- Evidence Manifest 完整，无缺失签名或无法复跑的 Gate 证据。

## Phase 1 预排

| ID | 工作项 | Responsible | Status | Depends On | Evidence ID | Needs User Decision |
|---|---|---|---|---|---|---|
| P1-01 | ADR 与 Trustable Core 边界冻结 | architect | backlog | Phase 0 | E-P1-01 | no |
| P1-02 | Contract fixtures 与失败验收测试 | qa | backlog | P1-01 | E-P1-02 | no |
| P1-03 | experimental `context-candidate/v0.1` + Validator | dev | backlog | P1-02 | E-P1-03 | no |
| P1-04 | 存储等级与 Git 泄露门禁 | dev | backlog | P1-02 | E-P1-04 | no |
| P1-05 | 稳定 ID、幂等、CAS、事务/恢复内核 | dev | backlog | P1-03/P1-04 | E-P1-05 | no |
| P1-06 | `init / validate / doctor / adopt` | dev | backlog | P1-05 | E-P1-06 | no |
| P1-07 | 安全与恢复集成验收 | qa + architect | backlog | P1-03..06 | E-P1-07 | no |
| P1-08 | 真实 KnowledgeBase 演练 | primary | backlog | P1-07 | E-P1-08 | remediation-only |
| P1-09 | Phase 1 Gate Review | primary + independent reviewers | backlog | P1-08 | E-P1-09 | go-no-go |

P1-02 必须保存 RED 证据；P1-03 至 P1-06 的每项实现必须映射至少一个先失败、后通过的验收测试。Gate 检查不得存在 skip/pending 测试；总体分支覆盖率下限为 80%，P1-01 ADR 只能提高、不能降低；安全与策略分支要求 100% fixture 覆盖。覆盖率报告必须登记到 Evidence Manifest。

## 已批准约束

以下内容来自已批准战略，不重复请求用户：

- Phase 1 `remote_model` 默认拒绝；
- Contract 随公开仓库存在但标记 `experimental`；
- `adopt/doctor` 优先支持当前真实 KnowledgeBase，对第三方库不自动迁移；
- Social Memory 排除出 Phase 1 公共 Contract；
- Phase 1 正式写入均需显式 accept。

## 待 Threat Model 后生成的决策包

当前仅预留一个可能的 D2 主题：**删除与保留承诺**。Architect 必须先说明正文、缓存、派生索引、审计日志、Git、备份、导出和远端副本各自可删除范围、保留期、完成时限与验证方式；primary 再判断是否仍需用户取舍。若最小诚实承诺可直接由现有红线推导，则记录为 D1 ADR，不打扰用户。

## 外部设计伙伴协议

- primary/pm 准备候选画像、邀请文案、知情同意和访谈 rubric；
- 用户只需提供或确认最多 3 名候选，并完成 Agent 无法代理的引荐；
- 未经用户显式授权，Agent 不直接联系任何外部人员；
- 纪要使用匿名 ID，不记录私有正文；证据包括同意状态、问题 rubric、核心问题确认结果和日期；
- P0-07 材料完成且邀请实际发出后，P0-08 才转为 `waiting_external`；邀请发出 7 日后仍不足 2 名，Phase 0 Gate 延期/no-go，不降低要求。

## 状态更新规则

- project-manager 在关键动作后更新本看板和 `process.md`，primary 复核；
- 每项任务必须在 Evidence Manifest 中有完整记录才能标记 done；
- 只有 `Needs User Decision` 非 `no` 的项目可生成用户请求；
- Phase 0/1 不因新想法扩 scope，新想法进入 backlog。
