# GoldenWave Roadmap

> 战略：个人验证后正式发布。仓库保持公开，但在真实 KnowledgeBase 闭环和外部设计伙伴验证前，Contract/API 均为 `experimental`。
>
> 完整决策、指标协议与风险见[产品战略与迭代规划](docs/prd/goldenwave-strategy/PRD.md)。

## 北极星

同一份用户拥有的上下文，能够被至少两个不同 Agent 正确、安全、可追溯地消费，并在任务结束后形成受治理的增量。

## 接口与边界

- CLI 优先，MCP 后置；CLI、Skill 和未来 MCP 必须复用同一 Contract、Policy 与 Validator。
- GoldenWave 负责 Store / Govern / Serve / Learn，不负责 Agent Runtime、任务编排、编辑器或全量捕获。
- 所有自动学习只产生 Candidate，不能绕过 review/accept/reject 修改正式层。
- 五层架构是信息模型；近期交付以端到端黄金路径为组织方式，不按层堆功能。

## v0.1 — Standard & Skeleton（已完成）

- [x] SPEC 与 L1-L5 分层规范
- [x] 初始化脚本与 Markdown 骨架
- [x] goldenwave-init / knowledge / profile Skills
- [x] 摄入路由 Skill 与 `_pending/` 草稿约定
- [x] Social Memory PRD、领域模型和分级存储设计（设计资产，实施延后）

## Phase 0 — Strategy & Baseline（当前，收口中）

**目标**：统一产品定义，建立可审计的 dogfooding 基线。

- [x] 确认“可信个人上下文治理层”定位
- [x] 确认“个人验证后正式发布”路径
- [x] 形成优劣势、四内核、指标与阶段 Gate
- [x] 同步 README、SPEC、Roadmap、摄入 PRD 与 Social Memory 状态
- [x] 输出 Threat Model：信任边界、攻击面、权限矩阵、恢复目标
- [x] 建立 20 个真实任务、20 个可重放 Oracle 与 120 条黄金断言
- [x] 记录人工代理流程基线：重复解释、错误类型、首次闭环时间
- [x] 准备设计伙伴协议与访谈材料
- [ ] 并行招募 2 名外部设计伙伴并完成概念/安装访谈

**内部开工 Gate**：文档无定位冲突；人工基线可复核；任务集覆盖 Profile、Knowledge、Project；Threat Model 通过评审。通过后可进入内部 Phase 1A dogfood，不再为等待外部引荐而闲置。

**外部验证 Gate**：两名设计伙伴知情同意并确认核心问题存在。它阻塞公共产品结论、稳定兼容承诺和正式发布，不阻塞内部 Phase 1A 实现与验证。

## Phase 1 — Trustable Core（按三个可独立验收的切片推进）

**目标**：将规范变为可确定运行的本地治理内核。

### Phase 1A — Safe Bootstrap

- [x] 实现安全的 `init` 与只读 `doctor`；
- [x] 实现 `git_tracked / local_private / ephemeral` 基础诊断和 Git 泄露门禁；
- [x] 对现有 KnowledgeBase 执行只读 adopt inventory，不自动修复；
- [x] 覆盖危险路径、symlink、非空目标、日志脱敏和私有文件误跟踪测试。

**1A Gate**：新库重复初始化幂等；真实 KnowledgeBase 可获得诚实诊断；敏感信息误入 Git 为 0；doctor 不修改、暂存或提交用户文件。

状态：2026-07-27 内部 Gate 已通过；Contract 继续标记为 `experimental`，外部验证仍待 P0-08。

### Phase 1B — Candidate Contract

- [ ] 发布 experimental `context-candidate/v0.1`、合法/非法 fixtures 和 Validator；
- [ ] 实现来源、新鲜度、内容/指令分离与稳定错误码；
- [ ] 实现最小 `review / accept / reject`，只允许显式接受后的单候选写入。

**1B Gate**：Contract fixture 可确定判定；未确认、来源不足、恶意或过期候选均 fail closed；所有正式写入可追溯。

### Phase 1C — Reliable Inject

- [ ] 实现稳定 ID、幂等键、CAS 与事务式多文件写入；
- [ ] 实现崩溃恢复、并发、备份恢复和审计链测试；
- [ ] 在前述内核通过后增加受控 adopt 修复与迁移。

**Phase 1 总 Gate**：1A/1B/1C 各自 Gate 通过；安全与恢复测试无 skip/pending；真实 KnowledgeBase 演练通过。统一 `goldenwave` CLI 随切片逐步形成，不作为先搭空壳的独立工作项。

## Phase 2 — Cross-Agent Golden Path（3-4 周）

**目标**：证明一份上下文能被不同 Agent 可信使用。

- [ ] 实现 `context build` 与 experimental `Context Pack v0.1`
- [ ] 携带来源、新鲜度、权限和最小必要内容
- [ ] 提供 Claude Code 与 Codex Adapter
- [ ] 实现 `candidate review / accept / reject` 与语义 diff
- [ ] 建立 prompt injection、上下文投毒与外传对抗集
- [ ] 运行 20 个真实任务的双 Agent 对照评测
- [ ] 两名外部设计伙伴各完成 3 个 sandbox 任务

**Gate**：Cross-Agent Task Success >=90%；Context Correctness >=95%；Time to First Governed Value <=15 分钟；对抗集零高危失败；写入全程可追溯。

## Phase 3 — Governed Learning Loop（4-6 周）

**目标**：证明 GoldenWave 能从真实使用中形成可验证复利。

- [ ] 从 Agent Run 提取 fact / knowledge / decision / pitfall Candidate
- [ ] 记录来源、语义 diff、拒绝原因与回放证据
- [ ] 定义 Experience 到 Knowledge / Skill Revision Candidate 的晋升协议
- [ ] 完成 Malow 最小 producer 集成
- [ ] 对重复任务运行质量、成本和回归评测

**Gate**：至少 15 个真实候选闭环，其中 >=10 个 accepted；>=6 个 accepted candidate 在预登记后续任务中正确复用；Governed Learning Rate >=60%；黄金任务无显著回归。

## Phase 4 — Domain Proof（4-6 周，按证据选一）

Phase 3 后按连续 30 日数据选择：

- Skill/Workflow Candidate 占 reviewable Candidate >=60%：优先 Skill Governance；
- 关系上下文请求占登记任务 >=30%，且隐私门禁通过外部评审：可选 Social Memory；
- 均不满足：延长 Phase 3，不强行扩域。

领域扩展必须复用公共来源、授权、确认、审计、版本、幂等和撤回接口，并通过 canary、active-base CAS、回滚与失败恢复演练。

## Phase 5 — Open-Source Productization（3-4 周）

**进入条件**：个人真实闭环稳定；两名外部设计伙伴完成黄金路径；兼容、安全和迁移策略明确；个人硬编码假设已移除。

- [ ] 提供可重复的安装和干净环境验证
- [ ] 发布首个稳定 Contract、兼容矩阵和迁移指南
- [ ] 发布威胁模型、安全边界、导出/删除/恢复文档
- [ ] 完善示例、故障排查、贡献指南和 release notes
- [ ] 两名外部用户在 release candidate 上复测黄金路径

**Release Gate**：安装、迁移、恢复、安全和黄金任务测试全部通过；外部用户复测通过；所有 P0/P1 缺陷关闭；稳定 Contract 的兼容与弃用策略已发布。

## 延后且不预先承诺

- 完整 Social Memory 应用与 `social-memory-patch`
- 公共 Skill / Workflow Registry
- 微信、IM、OS 级被动 Connector
- L4 Persona Instance 与 Agent Loop
- 写入型 MCP

这些方向只有在前序 Gate 和真实数据支持时才进入实施规划。

## 设计红线

1. 用户拥有正式上下文，核心价值不依赖单一 Agent 或托管服务；
2. 语义层与存储等级分离，需要硬删除的数据不得进入 Git；
3. 所有自动学习先产生 Candidate，不静默修改正式资产；
4. Context Pack 遵循最小必要原则并携带来源、新鲜度和权限；
5. Runtime 负责执行，GoldenWave 负责上下文治理；
6. 标准由运行实现和真实任务验证，个人实践不自动等于公共标准。
