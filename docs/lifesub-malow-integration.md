# LifeSub、Malow 与 GoldenWave 集成合同

- 状态：跨仓库关系基线；可执行 Contract 分阶段发布
- 日期：2026-08-14
- 范围：定义声音证据、项目处理、人工确认与长期上下文治理的所有权和依赖方向

## 1. 关系结论

三者是独立发布、独立存储、通过版本化 Contract 协作的并列项目：

> **LifeSub 记录现实，Malow 处理工作，GoldenWave 治理长期上下文。**

```text
LifeSub
  owns: Audio / Transcript / Session / Evidence Contract
                         |
                         v
Malow
  owns: Project / Matter / Organizer / Human Review
                         |
                         v
GoldenWave Inbox
  accepts: user-confirmed Knowledge Patch
                         |
                         v
GoldenWave Knowledge Governance Workflow
  owns: route / score / conflict / render / inject / git audit
```

Malow 可以作为 LifeSub ASR 结果的主要处理层，但不是所有 LifeSub 内容的强制中间层。项目型内容优先由 Malow 结合 Project / Matter 上下文整理并人工确认；非项目型个人记录可以由 LifeSub 在独立人工确认后直接提交 GoldenWave Inbox。

## 2. 责任与数据权威

### 2.1 LifeSub

LifeSub 负责录音、ASR、说话人、时间戳、Session、Transcript、Evidence Segment、检索、证据回溯和音频访问授权。LifeSub 是这些对象的唯一权威。

LifeSub 可以产生 Session Digest 或 Memory Candidate，但它们必须标记为未治理候选。LifeSub 不维护 Project / Matter 状态，不建立 GoldenWave Profile / Knowledge / Persona 副本，也不能直接修改正式层。

### 2.2 Malow

Malow 负责 Project、Matter、Conversation、Agent Run、Artifact、Organizer、Context Plan、Human Review 和 Knowledge Patch Draft。

Malow 通过 LifeSub Evidence Contract 消费证据，只保存稳定引用、hash、授权范围和必要快照；它把 LifeSub ASR 结果治理为有来源的候选内容，允许用户接受、修改、拒绝或拆分。人工接受只授权提交候选，不代表 GoldenWave 已经正式接纳。

### 2.3 GoldenWave

GoldenWave 负责 Knowledge Patch Contract、validator、兼容策略、候选路由、证据分级、敏感度、新鲜度、冲突处理、render、confirm、inject、Git 审计和治理回执。

只有 GoldenWave Knowledge Governance Workflow 可以把 Inbox envelope 转换为正式 L1 Profile、L2 Knowledge、Persona 或 L4 Project Context。Validator 成功、Malow Review 接受或文件写入成功都不能替代正式治理。

## 3. Contract 所有权

### 3.1 LifeSub Evidence Contract

- 所有者：LifeSub。
- 定义 Session / Segment / Evidence Bundle 的稳定 URI、内容 hash、时间范围、说话人、敏感级别、授权和撤回语义。
- Malow 是 consumer；GoldenWave 默认只保存来源引用，不主动复制完整证据。

### 3.2 GoldenWave Knowledge Patch Contract

- 所有者：GoldenWave。
- Malow 与 LifeSub 都可以是 producer。
- Envelope 必须包含 producer、完整 `contract_version`、稳定幂等键、目标层、候选内容、人工确认信息和 source refs。
- 当候选来自 Malow 对 LifeSub 证据的处理时，必须同时保留 Malow Project / Matter / Message / Run refs 与 `lifesub://` Evidence Ref。

## 4. 标准路径

### 4.1 项目型记录

```text
LifeSub Evidence
  -> Malow Matter / Organizer
  -> Human Review
  -> GoldenWave Knowledge Patch
  -> Inbox
  -> Knowledge Governance Workflow
```

### 4.2 非项目型个人记录

```text
LifeSub Candidate
  -> independent Human Review
  -> GoldenWave Knowledge Patch
  -> Inbox
  -> Knowledge Governance Workflow
```

无长期价值或未获确认的内容留在 LifeSub，不进入 GoldenWave。

## 5. 禁止事项

- 不共享数据库或共同维护领域状态机。
- 不以 submodule、vendoring 或锁步发布代替 Contract。
- Malow 不复制原始音频和完整 Transcript 数据库。
- LifeSub 不维护 Project / Matter / Agent Run。
- GoldenWave 不主动扫描全部录音，也不保存完整会议流水。
- Malow 与 LifeSub 不直接修改 GoldenWave 正式层。
- GoldenWave 不把 producer 的 `accepted` 状态映射为自动 inject。

## 6. 与现有 Malow 合同的关系

[GoldenWave 与 Malow 集成合同](malow-integration.md)继续定义 Malow producer、运行时 Knowledge Base 和发布兼容流程；本文在其上增加 LifeSub Evidence 上游及三项目的端到端边界。两份文档冲突时，更新日期更晚且范围更具体的条款优先，并应同步修订另一份文档。
