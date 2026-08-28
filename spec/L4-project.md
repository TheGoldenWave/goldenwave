# L4 — Project 规范（执行层）

> 为某个目标做事的容器。多数为 v0.3+ 预留，v0.1 仅定义边界。

## 定位
- Project = 一个目标的执行容器（含目标、任务、可运行 Skill）。
- 与 Workflow 区别：Workflow 是"层间怎么流转"（动词/管道）；Project 是"某目标的执行容器"（名词）。

这里的 Workflow 特指 L3 知识治理工作流（Knowledge Governance Workflow）。Malow 的项目工作流（Project Workflow）属于外部 Project Runtime 的执行编排，不作为 GoldenWave L3 对象保存；它产生的 Skill / Workflow Revision Candidate 可以通过 L3 Contract 进入治理。

## Skill 与 Project 经验晋升

- Skill 是程序性知识，描述一类工作怎么做，不等同于权限或凭据。
- Project 内形成的专属 Skill Revision 默认只属于该 Project；不能因一次成功运行自动全局化。
- 跨 Matter、跨 Project 重复验证后，可以提交带来源、评测、语义 diff 和回滚计划的 Skill Revision Candidate 或 Project Workflow Template Candidate。
- GoldenWave 通过 Knowledge Governance Workflow 确认后，才形成可跨工具复用的全局 Skill Revision 或 Project Workflow Template Revision；后者仍属于 L4 执行能力，不转化为 L3 Workflow。
- 全局 Skill 被 Malow 关联时仍需 Project / Matter Capability Binding 和 Run Capability Lease；Skill 本身不授予权限。

## 人格实例（Persona-as-skill）
- 可运行的"我的数字副本"（用我口吻起草/说话）属于此层，**不属于 Profile**。
- 它是由 `profile/persona/`（描述，SSOT）**编译**出的产物。
- 实例可重新生成；描述是唯一可信源。

## v0.3+ 预留
- 目标/任务看板（借 OpenHuman Goals & Todos）
- Agent Loop 自迭代（目标→执行→Oracle 验证→迭代）
