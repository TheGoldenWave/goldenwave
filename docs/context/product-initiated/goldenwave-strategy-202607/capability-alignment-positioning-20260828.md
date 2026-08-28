# GoldenWave Capability Alignment 定位与职责

状态：已确认跨项目职责，具体 Schema 与交互待实验验证

日期：2026-08-28

## 1. 决策摘要

Capability Alignment 如果归属一个现有方向，归 GoldenWave 管理状态与治理；学习任务、实践过程和 Outcome Review 由 Malow 执行。

> **GoldenWave 回答“人和 AI 分别会什么、依据是什么、何时可以协作或委托”；Malow 回答“如何通过学习和真实工作证明这些能力”。**

这不新增第五个 Authority，也不把 GoldenWave 扩张为课程平台。Capability Alignment 是 GoldenWave Memory Governance 的长期能力，教材生成器、导师 Agent、测验和练习是可替换 Capability。

## 2. 为什么归 GoldenWave

Capability Alignment 的长期对象包括：

- 人对某项知识或能力的掌握状态；
- Agent / Skill 对该能力的可用性、验证程度和失败模式；
- 人是否保留监督能力，以及允许的委托等级；
- 学习、测验、真实 Run 和 Outcome 形成的证据；
- 跨 Project、跨 Agent、跨 Runtime 的最近验证时间和状态变化。

这些对象必须长期保存、可追溯、可撤回并服务多个 Agent，符合 GoldenWave Store / Govern / Serve / Learn 的职责。Malow 的 Matter、Run 和 Review 是证据来源，不应成为跨项目 Capability Profile 的唯一存储。

## 3. 建议状态模型

首轮实验使用派生视图，不直接修改正式 Contract：

```text
Capability Profile
- capability_id
- human_state: unseen | aware | understood | practiced | proficient
- agent_state: unavailable | available | validated | delegated | unreliable
- supervision_requirement
- evidence_refs
- known_failure_modes
- last_verified_at
- learning_next_step
```

约束：

- `opened`、`read` 或点击“已学”不能直接变成 `understood`；
- `understood` 不能自动变成 `practiced`；
- Agent 安装了 Skill 不能自动变成 `validated`；
- `delegated` 必须有真实任务成功率、权限边界、验收方式和升级机制；
- 任何状态变化都要保留 Evidence Ref 和产生者。

## 4. 跨项目闭环

```text
Follow-up Signal / GoldenWave Candidate / 用户目标
  → learn_requested
  → GoldenWave 判断是否需要形成学习候选
  → Malow 创建 Learning Matter / Practice Run
  → Tutor Capability 生成概览、案例、测验或练习
  → 用户解释、选择或完成真实任务
  → Malow Outcome Review
  → GoldenWave 接收 Capability Evidence Candidate
  → Govern 后更新 Capability Profile
```

## 5. Capability Registry 本地实现

参考 Boujoy Harness 的 Markdown Expert / Style Registry 与本地 Vault 访问机制，Capability Profile 采用文本优先、渐进读取的本地投影：

- frontmatter 保存稳定 ID、版本、状态、最近验证时间和监督要求，正文保存能力说明、失败模式与证据摘要；
- Registry 列表只读取 compact metadata，搜索命中或构建 Context Pack 时再按需加载完整记录；
- 写入先生成 Capability Evidence Candidate，经 Govern 后原子更新正式投影；
- Adapter 使用可写路径白名单、Vault 边界校验、符号链接校验和临时文件替换；
- 更新与删除保留可恢复记录，索引作为可重建派生物随正式投影刷新；
- Malow Run / Outcome、Skill 版本和评测结果通过 Evidence Ref 关联，不复制运行时日志。

首轮派生报告可以直接基于 Markdown Registry 生成，Schema 验证通过后再固化到正式 Contract。

## 6. 职责矩阵

| 系统 | 负责 | 不负责 |
|---|---|---|
| Follow-up | 发现值得学习的 Signal，记录 `learn_requested`，提交带来源的 Handoff | 判断用户已经理解、保存课程进度 |
| GoldenWave | Capability 身份、Human/Agent 状态、证据、治理、跨 Agent Serve | 运行课程、执行练习、维护 Matter |
| Malow | Learning Matter、Practice Run、Artifact、Question、Review、Outcome | 静默修改长期掌握状态 |
| LifeSub | 必要时提供讲解、交流、现场实践或设备结果的 Evidence | 判断能力是否掌握 |
| Tutor Capability | 生成讲解、案例、测验和练习 | 成为正式状态权威 |

## 7. 与 GoldenWave Learn 的关系

GoldenWave 的 Learn 内核需要区分两个子方向：

- **System Learning**：从 Agent Run 中提取 Knowledge、Experience、Skill Revision Candidate。
- **Human-AI Alignment**：治理人和 Agent 的能力状态、监督关系和证据。

两者共享 Candidate、Evidence、Promotion 和撤回机制，但不能用“系统已收录”代替“人已掌握”。

## 8. 最小验证

1. 选择本人近期使用的 10 个 Skill 或概念，不新增正式 Schema，先生成 Capability 派生报告。
2. 标注 Human State、Agent State、最近调用、返工和失败模式。
3. 选择其中 5 个未掌握但工作相关的能力，生成 5 分钟材料和一个 Malow 实践 Matter。
4. 用解释题、真实任务和一周后找回验证 `understood`、`practiced` 与 `validated`。
5. 只有结果显著改善检索、委托或监督判断，才进入 Contract / PRD。

## 9. 非目标

- 不建设通用 LMS、课程商城或内容社区；
- 不把所有知识强制变成课程；
- 不用自评或点击替代实践 Evidence；
- 不让 GoldenWave 接管 Malow Runtime、Matter 或 Outcome；
- 不因 Capability Alignment 扩张当前 GoldenWave 黄金路径。
