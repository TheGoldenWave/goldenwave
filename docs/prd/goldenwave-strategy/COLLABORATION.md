---
feature_id: goldenwave-strategy
document: collaboration-charter
status: active
updated: 2026-07-24
---

# GoldenWave 人机协作章程

## 1. 协作目标

用户只负责少量不可逆、会改变产品承诺或风险边界的决策。主 Agent 代理项目负责人，负责拆解、委派、推进、评审、验收、状态维护和风险收口。

默认规则：

> **非 Gate 不打扰用户；凡需用户决策，必须附推荐答案、替代方案、影响和最晚决策点。**

## 2. 角色与责任

| 角色 | 核心职责 | 不负责 |
|---|---|---|
| 用户 / Product Owner | 产品承诺、隐私边界、不可逆取舍、Phase Gate | 跟踪子任务、审查普通实现、手动整理状态 |
| 主 Agent / Delivery Lead | 唯一协调入口；维护看板；拆任务；调度角色；整合冲突；向用户提交决策包 | 在未经授权时改变产品范围或对外承诺 |
| pm-agent | 需求口径、设计伙伴材料、访谈归纳、业务验收 | 写业务代码 |
| project-manager-agent | WBS、依赖、风险、里程碑、周报 | 改需求或实现代码 |
| architect-agent | Threat Model、ADR、接口边界、架构与安全审查 | 常规 CRUD 实现 |
| dev-agent | 按任务包执行 TDD、实现和自检 | 自行改变 SPEC 或 Gate |
| qa-agent | 先写验收测试、维护 fixtures/Oracle、执行 Gate | 降低失败标准以让任务通过 |
| spec reviewer | 独立检查产物是否满足已冻结任务包；由非作者 qa/architect/code-reviewer 担任 | 评价未写入任务包的个人偏好 |
| code reviewer | 独立检查实现质量、安全和维护性；不得是实现者 | 替实现者直接修复问题 |

### RACI

| 活动 | Accountable | Responsible | Independent Reviewer |
|---|---|---|---|
| 看板、process 与周报 | primary | project-manager | primary 复核状态证据 |
| 产品需求与外部访谈 | primary | pm | qa 检查问题与证据口径 |
| Threat Model / ADR | primary | architect | 非作者 architect 或 code-reviewer |
| 验收规格与 Oracle | primary | qa | architect 检查安全覆盖，pm 检查业务代表性 |
| 业务实现 | primary | dev | spec reviewer -> code reviewer |
| Phase Gate | 用户 | primary 汇总 | architect + qa 独立签署，作者不得自审 |

## 3. 风险分级开发闭环

任务先按影响分级，再选择与风险匹配的闭环，避免所有改动都支付相同治理成本。

| 等级 | 适用范围 | 最小闭环 |
|---|---|---|
| A — 高风险 | 安全策略、Contract、正式写入、权限、Git、恢复 | QA 先写失败验收 -> 实现 -> spec review -> code review -> 集成验收 |
| B — 中风险 | 确定性内部模块、只读诊断、CLI 编排 | 测试先行 -> 实现 -> 一次独立 review -> 集成测试 |
| C — 低风险 | 文档同步、状态更新、生成物、无行为重构 | 作者自检 -> `git diff --check`/相关校验 -> 主 Agent 复核 |

A 级任务采用完整闭环：

```text
主 Agent 冻结任务包
  -> qa-agent 先写失败验收测试
  -> dev-agent 实现并自检
  -> spec reviewer 检查是否满足任务包
  -> code reviewer 检查质量、安全和维护性
  -> 主 Agent 跑集成测试并更新看板/process.md
```

- B/C 级任务不得为了形式完整额外创建重复 Oracle、双重评审或独立状态文档。
- 实现任务默认串行，只有文件所有权不重叠且接口已冻结时才并行。
- 审查最多自动修正 3 轮；第三轮仍有 Major 问题时由主 Agent重新拆解，只有涉及产品取舍才升级用户。
- 失败必须保留可复核证据，不允许通过降低断言或删除测试收口。
- project-manager 负责更新看板/process，primary 对证据和最终状态负责；其他角色只提交任务结果，不直接宣布 Phase 完成。

### 仓库与分发边界

- `.agents/`、`.claude/`、`.codex/` 是维护者 Harness，不属于 GoldenWave 用户产品或 Knowledge Base 格式。
- 用户分发只包含产品运行所需的规范、CLI/脚本、Skills、模板与许可证；不得把完整维护者 Harness 当作安装依赖。
- 多 Agent 适配文件以单一源生成或同步，禁止长期手工维护内容相同的镜像副本。
- 已 vendored 的 bootstrap 资产在 Phase 0 收口后单独盘点；删除或迁移前先证明当前维护流程不再引用，避免以减重名义破坏 Agent 配置。

## 4. 用户决策分级

### D0：Agent 自主执行

无需用户确认：

- 文件组织、内部模块边界、命名和非公共 API；
- 测试结构、fixtures、错误码和审计事件字段；
- 稳定 ID、幂等键、CAS 与原子写入的具体实现；
- 不改变行为的重构、格式化、文档同步和缺陷修复；
- 在已批准 Gate 内的排期调整和 Agent 换手。

### D1：主 Agent 记录后执行

无需即时打扰用户，但必须写入 ADR/看板：

- 可逆的架构选型；
- experimental Contract 的向后兼容调整；
- 时间盒内的 scope 重排；
- Yellow/Orange 风险的缓解方案；
- 测试工具、运行时和依赖选择。

### D2：用户关键决策

必须给用户决策包：

- 改变产品定位、目标用户、北极星或 Phase Gate；
- 扩大远程模型、外发、自动写入或第三方数据权限；
- 对外稳定兼容承诺、正式发布或弃用公共 Contract；
- 无法完整回滚的数据迁移、历史 purge 或破坏性删除；
- 新增持续成本、外部服务、账号授权或公开沟通；
- 排期偏差超过 20%，且只能通过砍范围或降低标准解决；
- Threat Model 存在未缓解的 High/Critical 风险；
- Phase Gate 的 go / no-go。

## 5. 风险与升级

| 级别 | 定义 | 默认动作 |
|---|---|---|
| Green | 按计划，Gate 无风险 | 自动推进 |
| Yellow | 小幅滑动，不威胁 Gate | 主 Agent 自主重排并记录 |
| Orange | 阻塞 >1 工作日、证据缺失或跨角色冲突 | 主 Agent 当日给替代路径，不默认打扰用户 |
| Red | 威胁 Gate、数据安全或需 D2 决策 | 暂停相关写入，向用户提交单页决策包 |

Stop-ship：`Unsafe Persistence > 0`、恢复演练失败、Threat Model 未通过、测试被证明不足以覆盖 Gate。

外部事件使用 `waiting_external`，不按普通 Orange 阻塞计时。等待期间继续推进内部 Phase 1A；超过决策包约定期限仍无法获得两名设计伙伴时，外部验证与正式发布 Gate 自动延期，不降低样本要求，也不撤销已经通过的内部开工 Gate。

## 6. 用户沟通格式

主 Agent 只在以下时点主动请求用户：

1. 一组 D2 决策可以合并确认时；
2. Phase Gate 前；
3. 出现 Red 风险时；
4. 需要用户本人完成外部引荐、账号授权或无法代理的真实体验验收时。

每个决策包固定为：

```markdown
决策：一句话
推荐：主 Agent 推荐项
原因：最关键的 2-3 条证据
备选：其他可行方案及代价
不决定的影响：默认会暂停什么
最晚决策点：何时前需要确认
```

普通进度只报告结果、风险和下一里程碑，不转述 Agent 的过程对话。

## 7. 状态真相源

- 产品与 Gate：`docs/prd/goldenwave-strategy/PRD.md`；已批准修订按 `amendments/` 日期顺序覆盖对应章节
- 执行状态：`.artifacts/execution-board.md`
- 会话恢复：`.artifacts/process.md`
- 架构决策：`docs/context/technical/goldenwave/adr/`
- 测试与证据：`tests/specs/` 和 `tests/evidence/`
- 证据清单：`.artifacts/evidence-manifest.md`

聊天记录、Agent 消息和临时计划都不是项目状态真相源。
