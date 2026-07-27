# GoldenWave 核心术语中英对照

- 状态：跨工具术语基线
- 日期：2026-07-23
- 规则：中文主概念用于说明与交互；英文领域名用于 Schema、API、代码和首次解释

## GoldenWave 核心层

| 中文主概念 | English Domain Name | 定义 |
|---|---|---|
| 个人事实层 | Profile | 关于用户及与用户有关的当前事实、关系和人格描述 |
| 知识层 | Knowledge | 可复用、可迁移、带来源的长期知识 |
| 知识治理工作流 | Knowledge Governance Workflow | L3 中控制信息如何 capture、route、score、redact、confirm、inject 和 sync 的治理流转 |
| 项目层 | Project | L4 中围绕目标执行、产出和可运行 Skill 的范围 |
| 知识补丁合同 | Knowledge Patch Contract | 外部 producer 向 GoldenWave Inbox 提交候选的版本化协议 |
| 治理运行 | Governance Run | 一次知识治理工作流的实际执行与回执 |
| 正式沉淀 | Governed Injection | 通过来源、隐私、目标层和用户确认后进入正式层的写入结果 |

## Skill 与跨项目晋升

| 中文主概念 | English Domain Name | 定义 |
|---|---|---|
| 技能 | Skill | 固化“一类工作怎么做”的程序性知识 |
| 技能定义 | Skill Definition | Skill 可跨工具读取的稳定基础内容、触发边界和输入输出合同 |
| 技能版本 | Skill Revision | 经治理、评测、确认并可回滚的 Skill 版本 |
| 技能修订候选 | Skill Revision Candidate | 从 Project 实际运行中形成、尚未全局启用的改进提案 |
| 工作流修订候选 | Workflow Revision Candidate | 针对知识治理步骤、规则或模板的候选修改 |
| 项目工作流 | Project Workflow | Malow 等执行系统中围绕 Project 的阶段、依赖、Skill、MCP、预算和 Gate 编排；不属于 GoldenWave L3 |
| 项目工作流模板 | Project Workflow Template | 跨 Project 复用的执行编排骨架，可由 GoldenWave 治理和分发，但仍不属于 L3 治理管线 |

## 与 Malow 共用但不合并的概念

| 中文主概念 | English Domain Name | 边界 |
|---|---|---|
| 能力定义 | Capability Definition | Malow 用于描述 Skill、MCP、Project Workflow；GoldenWave 可以提供全局 Skill/Workflow 来源 |
| 能力绑定 | Capability Binding | Malow Project/Matter 的长期关联，不写入 GoldenWave 正式层 |
| 临时能力授权 | Capability Lease | Malow Run 的实际权限，不由 GoldenWave Skill 自动授予 |
| 运行证据 | Run Evidence | 结果、用户修正、Verifier、Outcome 和成本；可作为晋升候选证据 |
| 修订候选 | Revision Candidate | 进入 GoldenWave 前的带来源、评测和语义 diff 提案 |

## 两类 Workflow

### 项目工作流（Project Workflow）

负责某个 Project 内的执行编排，由 Malow 等 Runtime 定义和运行。它可以产出 Knowledge / Skill / Workflow Patch Candidate，但不能直接写入 GoldenWave 正式层。

### 知识治理工作流（Knowledge Governance Workflow）

负责候选如何进入 GoldenWave：

```text
capture -> route -> score -> redact -> render -> confirm -> inject -> audit
```

两者只共享版本、来源、证据、确认、幂等和回滚原则，不共享同一个领域类型。

跨 Project 成熟的 Malow Project Workflow 晋升为 Project Workflow Template，而不是 Knowledge Governance Workflow。只有直接修改 capture / route / score / confirm / inject 规则的候选，才属于 Knowledge Governance Workflow Revision。
