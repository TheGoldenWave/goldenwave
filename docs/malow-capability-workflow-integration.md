# Malow 能力演化与 GoldenWave Workflow 集成

- 状态：跨项目关系基线
- 日期：2026-07-23
- 关联：[GoldenWave 与 Malow 集成合同](malow-integration.md)

## 1. 定义边界

Malow 的项目工作流（Project Workflow）与 GoldenWave 的知识治理工作流（Knowledge Governance Workflow）是独立领域对象：

| 对比 | Malow Project Workflow | GoldenWave Knowledge Governance Workflow |
|---|---|---|
| 目的 | 编排 Project 内阶段、Agent、Skill、MCP、预算和 Gate | 治理候选如何分类、确认、写入和审计 |
| 运行范围 | Project / Matter / Work Cycle | 用户 Knowledge Base L1-L4 |
| 运行实例 | Workflow Run | Governance Run |
| 主要输出 | Artifact、Run Evidence、Revision Candidate | 正式 Knowledge、Profile、Skill / Workflow Revision 或拒绝回执 |
| 权限重点 | tool、resource、network、credential、budget | privacy、consent、target layer、retention、formal write |

代码与 Contract 不共用同一类型：Malow 使用 `ProjectWorkflowDefinition`，GoldenWave 使用 `KnowledgeGovernanceWorkflowContract`。

## 2. Skill / Workflow 晋升路径

```text
Matter 中的真实使用与用户修正
        -> Malow Revision Candidate
        -> 固定回放、Verifier、Outcome、成本和安全评测
        -> 用户确认 Project Revision
        -> 多个 Project 中继续验证
        -> GoldenWave Skill / Project Workflow Template Candidate
        -> Knowledge Governance Workflow
        -> 用户确认全局 Revision
```

原则：

- Matter 中学习，Project 中固化，跨 Project 后才建议全局化。
- Malow 可以自动收集证据、生成候选和执行沙箱评测，但不能静默修改 active Skill / Workflow。
- GoldenWave 不接受只有模型自评的晋升；候选必须包含来源、适用范围、语义 diff、旧/新版本对照、用户确认和回滚信息。
- 权限、网络、凭据和写入 scope 不属于 Skill Revision；它们留在 Malow Capability Binding / Lease，并需要独立确认。
- GoldenWave Skill 不因被安装或关联而自动获得 Malow Project/Matter 权限。

## 3. 候选合同

跨项目候选至少携带：

```text
candidate_id
candidate_kind: skill | project_workflow_template | knowledge_governance_workflow
source_projects
source_matters
base_definition / base_version
semantic_diff
evidence_refs
evaluation_summary
capability_environment_snapshot
resolved_capability_set_hash
definition_integrity_hashes
feature_flag_set_hash
lease_policy_snapshot_hash
mcp_schema_hashes
quality_delta
personalization_delta
token_and_latency_delta
safety_results
confirmed_project_revision
proposed_global_scope
rollback_plan
```

GoldenWave 接收候选只表示可治理，不表示自动成为全局 Skill / Workflow。正式启用必须产生新 Revision、确认记录和审计结果。

候选还必须携带 `base_revision_ref / base_revision_hash`。GoldenWave 激活新 Revision 时执行 active-base CAS；base 已过期则拒绝覆盖 newer active，要求基于最新版本 rebase 并重新评测。回滚创建新 Revision，不重新激活历史行。

`project_workflow_template` 用于跨 Project 复用执行编排；`knowledge_governance_workflow` 只用于 GoldenWave L3 治理管线自身的修改，两者不得互相转换或共用 Schema。

## 4. 反向复用

GoldenWave 中经过治理的 Skill / Workflow Revision 可以作为 Malow Capability Definition 来源：

```text
GoldenWave global revision
        -> Malow Capability Registry
        -> Project Capability Binding
        -> Matter Capability Overlay
        -> Run Capability Lease
```

Malow 固定版本和 integrity hash，不静默跟随 latest。GoldenWave 发布新版本后，Malow 只生成 upgrade proposal；用户确认后再切换，并保留上一版本回滚点。

## 5. 非目标

- GoldenWave 不运行 Malow Project Workflow。
- Malow 不复制 GoldenWave L3 Governance Runtime。
- 不从单次聊天直接生成并全局启用 Skill。
- 不用 Skill 内容携带或扩大权限。
- 不因 Token 更省就绕过质量、来源、隐私和安全 Gate。
