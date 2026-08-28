# GoldenWave 长期记忆基础设施：开放问题与验证议程

状态：待验证研究议程，不是 SPEC 或路线图承诺

日期：2026-08-25

来源：2026-08-24 三段个人 AI 产品沟通 ASR，以及 GoldenWave 的 Store / Govern / Serve / Learn 定位

## 0. 使用边界

本文用于后续 Agent 研究和实验，不直接改变 GoldenWave 的正式 Contract、Schema、成熟度枚举或路线图。任何新字段或状态必须先用真实 KnowledgeBase 样本验证，再进入 PRD、SPEC 和兼容性流程。

2026-08-28 已确认 Capability Alignment 的跨项目责任：GoldenWave 管状态与治理，Malow 执行学习、实践和 Outcome Review，Follow-up 只提交 `learn_requested`。具体设计见 `capability-alignment-positioning-20260828.md`；下列 Q-G1 至 Q-G3 继续验证状态模型、交互和效果，不再重新讨论顶层归属。

## Q-G1：AI 能使用某知识，但人没有理解，它属于“我的知识”吗？

### 问题定义

自动摄入会让知识库快速超过人的认知范围。AI 可以检索和回答，但用户没有读过、无法监督，也不知道何时主动调用。这会造成“系统很聪明、本人却失去知识边界感”的错位。

### 暂定模型

需要同时描述两个维度，而不是用单一 `status` 混在一起：

| AI 可用状态 | 人的掌握状态 |
|---|---|
| 未索引 / 可召回 / 已在任务中验证 | 未接触 / 已浏览 / 已理解 / 已实践 |

“AI 可召回”不能自动晋升为“人已理解”；“人已读”也不能证明内容真实或可复用。

### 最小实验

- 从当前 KnowledgeBase 抽取 30 页：本人熟悉、只浏览过、完全未读各 10 页；
- 让两个 Agent 用相同 Context Pack 完成任务，并让本人完成简短解释和应用题；
- 比较 AI 任务成功、人的自评、解释正确率和一周后找回率。

### 通过信号

能够用少量、稳定、可解释的状态区分“AI 有”“人会”“实践过”，并真实改善检索、学习安排或权限判断。

### 停止条件

如果状态主要依赖用户手工维护且一周内大面积过期，则不进入正式 Schema，只保留查询视图或派生报告。

## Q-G2：如何把 Candidate 变成个人学习闭环？

### 问题定义

发现值得保留的内容只是开始。若用户脑中没有索引，也没有在真实任务中应用，知识可能永远留在库里。对话提出了“5 分钟课程、案例、小测试、实践任务”的自适应学习形态。

### 候选闭环

```text
Candidate accepted
  → 判断本人是否需要理解
  → 生成 5 分钟概览或适配媒介
  → 解释 / 案例 / 小测试
  → Malow 创建实践 Matter 或任务
  → Outcome 证明是否真正掌握
  → 更新 human-understanding / practice evidence
```

### 已确认职责边界

- GoldenWave 拥有 Capability 身份、人/AI 掌握状态、学习证据和晋升治理；
- 教材生成器是可替换 Capability，不成为 GoldenWave 内核；
- Malow 承担 Learning Matter、Practice Run 和 Outcome Review；
- Follow-up 只产生带来源的 `learn_requested`，不能标记 `understood` 或 `practiced`；
- 不能用完成阅读或点击“已学”替代实践证据。

### 最小实验

选择 5 个本人近期未掌握但工作相关的 Skill/概念。每个生成 5 分钟材料和一个真实小任务，对比纯阅读与“阅读+实践”的一周后找回和使用表现。

## Q-G3：如何建立“人 + AI”的能力地图？

### 问题定义

Harness 中存在大量 Skill，但用户不知道它们在哪里、何时使用、是否可靠，以及自己需要理解到什么程度。Skill Registry 只回答“安装了什么”，没有回答“谁会什么”。

### 候选能力矩阵

| 状态 | 含义 |
|---|---|
| 人会、AI 会 | 可协作、可互相验证 |
| 人懂原理、AI 做细节 | 适合委托，人保留监督能力 |
| 人不会、AI 已验证 | 需要明确风险和升级机制 |
| 人会、AI 不稳定 | 适合积累训练/评测样本 |
| 双方都不会 | 能力缺口，不应伪装可用 |

每个 Capability 还需要版本、来源、评测、调用记录、权限、失败模式和最近验证时间。

### 最小实验

只盘点本人最常用的 20 个 Skill，统计过去 30 天主动调用、自动调用、成功、返工和本人理解状态。验证能力地图能否减少“装了但不会用”和重复安装。

### 跨仓依赖

Malow 负责真实 Run、学习实践、Outcome 和调用证据；GoldenWave 保存可迁移的 Capability Profile、Capability/Experience Candidate 和治理历史，不接管运行时 Registry。

## Q-G4：Decision / Outcome 何时应晋升为长期原则？

### 问题定义

单次拒绝 AI 建议不一定代表稳定偏好，单次成功也不应直接成为原则。需要区分情境选择、重复模式和经结果复盘后的长期认知。

### 暂定晋升链

```text
Malow Decision + Evidence
  → Actual Outcome
  → Retrospective
  → Experience Candidate
  → 多次一致或高价值单例验证
  → Principle / Preference / Procedure Candidate
```

### 必须避免

- 把一次行为静默推断为人格；
- 只记录结果，不保留当时可见证据和不确定性；
- 用事后结果反推当时决策必然正确或错误；
- 将专业高风险判断仅凭个人结果晋升为通用知识。

## Q-G5：谁控制模型路由，取决于 Memory 在谁手里吗？

### 问题定义

厂商可以提供统一 Agent 并代做模型路由，但如果长期 Memory 只存在其云端，用户很难判断路由是否符合自身利益，也难以迁移。用户自有 Memory 是路由自主权的前提，但不是充分条件。

### 需要验证的合同

- Memory 与 Provider / Model / Harness 解耦；
- Context Pack 记录选择依据、暴露范围和消费方；
- 更换 Agent 后无需迁移专有 Memory 即可完成同一黄金任务；
- 路由策略可以读取用户偏好，但不能泄露完整私有上下文；
- Provider 质量、成本和可用性变化可被追踪和复盘。

### 最小实验

用 Claude Code 与 Codex 消费同一组 Context Pack 完成 20 个真实任务，比较成功率、上下文正确性、敏感数据暴露和切换成本。

## Q-G6：健康、财务等领域数据应如何接入，而不把 GoldenWave 变成万能数据库？

### 问题定义

健康报告、财务时间序列和跨机构记录需要结构化 Schema、时间线、专用检索和专业责任，单纯 Markdown/RAG 不够。GoldenWave 应保存长期上下文，但不应复制全部领域数据。

### 暂定边界

- 外部 Domain Information System 仍是 source-of-origin；LifeSub 通过 Source Adapter 保存获授权的个人 Evidence、来源证明和稳定引用；
- GoldenWave 保存稳定引用、经过确认的事实、个人偏好、长期原则和 Context Pack；
- 高风险解释需要专业证据、时效和 Human/Professional Gate；
- 外部源或 LifeSub Evidence 删除、撤回或过期后，GoldenWave 必须能识别来源失效。

### 最小实验

先用 LifeSub 全领域 Evidence Contract 验证“外部 source-of-origin + LifeSub Evidence Ref + GoldenWave 受治理结论”，再评估健康或财务连接器，不直接在 GoldenWave 建设领域数据库。

## Q-G7：开源什么，才能增加影响力又不平替本人？

### 问题定义

开放协议和工具有助于社区采用，但个人 Memory、判断轨迹和经验包构成实际竞争优势。项目需要区分公共基础设施与私人能力资产。

### 暂定开放层级

| 层级 | 默认策略 |
|---|---|
| SPEC、Contract、Validator、通用 Harness | 开放 |
| 通用 Skill、评测方法、脱敏案例 | 可开放 |
| 专业 Capability 与经验包 | 按许可证和用途有限开放 |
| 个人 Profile、Memory、关系、Decision Trace | 私有 |

### 待验证问题

- 什么资产最能产生引用、Star、贡献和设计伙伴，而不是只增加维护成本？
- 能否通过公开 benchmark 和协议证明能力，而不公开个人数据与判断权重？
- 哪些私有经验可以编译成能力而不泄露原始 Memory？

## 建议研究顺序

1. Q-G1 人-AI 认知状态；
2. Q-G3 能力地图；
3. Q-G2 学习闭环；
4. Q-G4 Decision / Outcome 晋升；
5. Q-G5 Memory 与模型路由；
6. Q-G6 领域系统连接；
7. Q-G7 开源边界。

Q-G1、Q-G3 可先做派生报告，不修改正式 Contract；只有实验表明它们改善真实任务，才进入 Schema 设计。

## 来源

- `~/KnowledgeBase/.sources/inbox-processed/2026-08-24/08-24 个人AI事项管理.txt`
- `~/KnowledgeBase/.sources/inbox-processed/2026-08-24/08-24 AI产品竞争与个人知识管理.txt`
- `~/KnowledgeBase/.sources/inbox-processed/2026-08-24/08-24 AI代理整合与模型越狱.txt`
- `README.md`
- `SPEC.md`
- `docs/prd/goldenwave-strategy/PRD.md`
