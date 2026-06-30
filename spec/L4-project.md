# L4 — Project 规范（执行层）

> 为某个目标做事的容器。多数为 v0.3+ 预留，v0.1 仅定义边界。

## 定位
- Project = 一个目标的执行容器（含目标、任务、可运行 Skill）。
- 与 Workflow 区别：Workflow 是"层间怎么流转"（动词/管道）；Project 是"某目标的执行容器"（名词）。

## 人格实例（Persona-as-skill）
- 可运行的"我的数字副本"（用我口吻起草/说话）属于此层，**不属于 Profile**。
- 它是由 `profile/persona/`（描述，SSOT）**编译**出的产物。
- 实例可重新生成；描述是唯一可信源。

## v0.3+ 预留
- 目标/任务看板（借 OpenHuman Goals & Todos）
- Agent Loop 自迭代（目标→执行→Oracle 验证→迭代）
