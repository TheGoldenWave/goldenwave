---
feature_id: goldenwave-strategy
stage: phase-1c-complete
status: complete
updated: 2026-08-16
accountable: primary-agent
responsible_for_status: project-manager-agent
---

# GoldenWave 执行看板

## 当前里程碑

- **Phase**：1C — Reliable Inject（complete）
- **状态**：Green（P1B-03、P1C-01、P1C-02、P1C-03 Gate 均 pass）
- **目标**：Phase 1C 已完成；后续按 Roadmap 进入 Phase 2 或单独授权真实 KB remediation。
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
| P0-05b | 20 个真实 dogfood 任务与可重放 Oracle | qa | done | P0-03/P0-04 | E-P0-05b | representative-only |
| P0-06 | 人工代理流程基线 | qa + primary | done | P0-05b | E-P0-06 | no |
| P0-07 | 设计伙伴协议与访谈材料 | pm | done | P0-04/P0-05b | E-P0-07 | no |
| P0-08 | 设计伙伴名单、知情同意、引荐与访谈 | pm | todo | P0-07 | E-P0-08 | introduction-only |
| P0-09 | Phase 0 内部开工 Gate Review | primary + independent reviewers | done | P0-02..07 | E-P0-09 | go-no-go |

P0-05b 的规格与质量审查均已通过，用户已完成一次 suite-level 代表性与低敏字段确认；P0-06 已完成 `20` 个单响应人工代理 runs 的 repo scorecard 记录与独立复核，结果为 `96 pass / 24 fail / 0 invalid`，主要失败集中在 provenance 断言缺失。P0-07 已补齐邀请文案、知情同意、匿名字段与访谈 rubric；P0-09 已按 2026-07-27 减重修订案完成内部 Gate Review 并给出 `GO`。

### P0-03 盘点边界

现有用户授权已覆盖读取 `/Users/goldenwave/KnowledgeBase` 以支持 GoldenWave 规划。盘点默认只读取结构、索引、Schema、低敏 Profile 控制台和 Agent 接入配置：

- 不读取 `profile/` 中 L3 正文、`.private/`、财务、健康、亲友原始信息；
- 不复制个人正文到项目仓库；
- 输出仅含数量、类型、路径类别、风险和脱敏示例；
- 遇到无法从元数据判断的敏感文件，标记 unknown，不为完成盘点而展开正文。

### Phase 0 内部开工 Gate

- 定位、边界和红线无冲突；
- Threat Model 通过非作者评审；
- 20 个任务覆盖 Profile / Knowledge / Project，且 >=100 条断言可复核；
- 人工基线保留原始记录；
- Evidence Manifest 完整，无缺失签名或无法复跑的 Gate 证据。

当前状态：`passed on 2026-07-27`，详见 `E-P0-09`。

P0-08 调整为并行外部验证泳道：两名设计伙伴的知情同意和问题确认仍是公共产品结论与正式发布的必要证据，但不再阻塞内部 Phase 1A dogfood。

## Phase 1 预排（减重后）

| ID | 工作项 | Responsible | Status | Depends On | Evidence ID | Needs User Decision |
|---|---|---|---|---|---|---|
| P1A-01 | Safe Bootstrap 检查集与失败验收 | qa + architect | done | P0-09 | E-P1A-01 | no |
| P1A-02 | 安全 `init`、只读 `doctor` 与 Git 门禁 | dev | done | P1A-01 | E-P1A-02 | no |
| P1A-03 | 新库 + 真实 KnowledgeBase 只读演练与 1A Gate | primary + qa | done | P1A-02 | E-P1A-03 | remediation-only |
| P1B-01 | Candidate Contract、fixtures 与 Validator | qa + dev | done | P1A-03 | E-P1B-01 | no |
| P1B-02 | 最小 review/accept/reject 与单候选写入 | dev | done | P1B-01 | E-P1B-02 | no |
| P1B-03 | Contract 安全验收与 1B Gate | qa + architect | done | P1B-02 | E-P1B-03 | no |
| P1C-01 | 稳定 ID、幂等、CAS 与事务式 inject | dev | done | P1B-03 | E-P1C-01 | no |
| P1C-02 | 并发、崩溃、备份恢复与受控 adopt 修复 | dev + qa | done | P1C-01 | E-P1C-02 | remediation-only |
| P1C-03 | 真实库恢复演练与 Phase 1 Gate | primary + independent reviewers | done | P1C-02 | E-P1C-03 | go-no-go |

## 复杂度减重泳道

| ID | 工作项 | Status | Depends On | 完成标准 |
|---|---|---|---|---|
| CR-01 | 维护者 Harness 引用盘点与物理去重方案 | todo | - | 明确单一模板源、必要适配层、可删除镜像及验证命令 |
| CR-02 | 真实纵向闭环 | backlog | P1B-02 | `init -> context build -> candidate -> accept -> 后续复用` 有真实证据 |
| CR-03 | 状态来源收敛 | backlog | CR-01 | 同一状态不再由 README、ROADMAP、process、看板手工重复维护 |
| CR-04 | 对外认知路径简化 | backlog | CR-02 | 入口文档优先呈现五步用户路径，内部模型渐进披露 |
| CR-05 | Contract 单一结构定义 | backlog | P1B-01 | Schema 是基础结构 SSOT；运行时不复制字段和枚举；紧凑投影可生成 |
| CR-06 | 复杂度预算门禁 | backlog | CR-01/CR-03 | 新增治理资产需抵消旧机制或记录例外理由 |

每个切片先保存对应 RED 证据，再进入实现。Gate 检查不得存在 skip/pending 测试；总体分支覆盖率下限为 80%，安全与策略分支要求 100% fixture 覆盖。覆盖率报告登记到 Evidence Manifest，但不为低风险文档或生成物重复建立多层审查证据。

## 已批准约束

以下内容来自已批准战略，不重复请求用户：

- Phase 1 `remote_model` 默认拒绝；
- Contract 随公开仓库存在但标记 `experimental`；
- Phase 1A 的 `adopt/doctor` 优先支持当前真实 KnowledgeBase，保持只读且不自动迁移；
- Social Memory 排除出 Phase 1 公共 Contract；
- Phase 1 正式写入均需显式 accept。

## 待 Threat Model 后生成的决策包

当前仅预留一个可能的 D2 主题：**删除与保留承诺**。Architect 必须先说明正文、缓存、派生索引、审计日志、Git、备份、导出和远端副本各自可删除范围、保留期、完成时限与验证方式；primary 再判断是否仍需用户取舍。若最小诚实承诺可直接由现有红线推导，则记录为 D1 ADR，不打扰用户。

## 外部设计伙伴协议

- primary/pm 准备候选画像、邀请文案、知情同意和访谈 rubric；
- 用户只需提供或确认最多 3 名候选，并完成 Agent 无法代理的引荐；
- 未经用户显式授权，Agent 不直接联系任何外部人员；
- 纪要使用匿名 ID，不记录私有正文；证据包括同意状态、问题 rubric、核心问题确认结果和日期；
- P0-07 材料完成且邀请实际发出后，P0-08 转为 `waiting_external`；等待期间继续内部 Phase 1A。两名设计伙伴证据不足时，公共产品结论与正式发布 Gate 延期，不降低要求，也不反向阻塞只读诊断和安全初始化的内部 dogfood。

当前状态：P0-07 已完成，P0-08 尚未记录真实邀请发送或用户引荐，因此保持 `todo`。

## 状态更新规则

- project-manager 在关键动作后更新本看板和 `process.md`，primary 复核；
- 每项任务必须在 Evidence Manifest 中有完整记录才能标记 done；
- 只有 `Needs User Decision` 非 `no` 的项目可生成用户请求；
- Phase 0/1 不因新想法扩 scope，新想法进入 backlog。
