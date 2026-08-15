---
feature_id: goldenwave-strategy
document: approved-amendment
status: active
approved: 2026-08-10
---

# 复杂度减重与结构定义修订案

## 决定

GoldenWave 保留隐私、来源、确认、安全写入和恢复等产品差异化内核，同时把近期工程目标收敛为真实用户纵向闭环。新增流程、角色、规范或状态载体必须证明其收益高于维护成本；默认优先删除、合并或生成现有机制。

## 执行顺序

1. 盘点并物理去重维护者 Harness，只保留一个模板源和必要的 Claude/Codex 薄适配层。
2. 暂停扩展 Social Memory、Malow、Persona 等支线，优先完成一次真实的 `init -> context build -> candidate -> accept -> 后续复用`。
3. 收敛项目状态来源，使 README、ROADMAP、process 和执行看板不再手工重复维护同一状态。
4. 对外以“收集 -> Candidate -> 人工确认 -> 写入 -> 按任务提供上下文”为主要认知路径；L1-L5、权限矩阵和存储等级作为进阶规范。
5. Contract 采用单一结构定义来源，运行时代码不再手工复制字段、枚举和基础结构约束。
6. 引入复杂度预算：新增一个规范、角色或状态文件时，必须同步删除、合并、自动生成一项旧机制，或记录无法抵消的理由。

## Contract 格式原则

- `context-candidate/v0.1` 当前继续以 JSON Schema 作为结构定义的单一真相源。
- Python Validator 只保留 JSON Schema 难以或不适合表达的跨字段、安全和运行时语义；字段、枚举、必填项等基础约束应从 Schema 读取或生成。
- 不因 Schema 文件本身较长而立即更换格式。Schema 是低频定义资产，Candidate 实例才是高频存储和传输载荷，两者分别评估。
- 若 LLM 上下文存在可测量的 token 成本，从 JSON Schema 自动生成紧凑字段投影；该投影是生成物，不得成为第二真相源。
- 替代格式只有在真实 Candidate 样本上同时证明字符/token 更少、约束表达足够、工具链更简单且不降低可审计性时，才进入 Contract 变更决策。

## 近期非目标

- 不为了格式更短同时维护 JSON Schema、CUE、JTD、YAML Schema 或自定义 DSL。
- 不在真实闭环完成前扩建新的 Agent 角色、Gate、证据层或领域 Contract。
- 不以删除安全测试、来源约束、显式确认或恢复能力作为减重手段。
