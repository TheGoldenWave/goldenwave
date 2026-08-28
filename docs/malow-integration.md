# GoldenWave 与 Malow 集成合同

- 状态：跨仓库关系基线，首个可执行 Contract 待发布
- 日期：2026-07-23
- 范围：定义 GoldenWave、Malow 与用户 Knowledge Base 的所有权、协议依赖和同步迭代方式

## 1. 关系结论

GoldenWave 与 Malow 是并列、独立发布的源码项目，不使用 Git submodule，也不互相 vendoring 整个仓库。

三者关系如下：

```text
GoldenWave source repository
  owns: Knowledge Patch Contract / validator / compatibility policy
                         |
                         v
Malow source repository
  owns: Project / Matter / Review / GoldenWave Adapter
                         |
                         v
User Knowledge Base
  owns: Inbox envelopes / formal knowledge / independent Git history
```

依赖方向是 `Malow -> GoldenWave Contract`：GoldenWave 是上游协议所有者，Malow 是下游 Knowledge Patch producer。用户通过 `scripts/init.sh` 创建的 Knowledge Base 是运行时数据，不是任一源码仓库的 submodule。

## 2. 责任边界

### 2.1 GoldenWave

GoldenWave 负责：

- 定义 Knowledge Patch envelope、目标层语义、必填字段和验证规则。
- 发布版本化 JSON Schema、合法/非法示例、validator 和变更说明。
- 定义幂等键、来源、确认时间、冲突信息和处理回执的协议语义。
- 保持协议工具中立，使 Malow 之外的 producer 也能实现同一合同。
- 对破坏性变更提升 Contract 主版本，不用隐式目录变化改变协议。
- 区分“envelope 已验证/已接收”和“内容已路由进入 L1/L2/L4”；validator 成功不能替代 GoldenWave 的 route、score、render、确认与 inject。

### 2.2 Malow

Malow 负责：

- 保持 Project、Matter、Organizer、Review 和 Knowledge Patch 领域语义独立于 GoldenWave 内部目录。
- 通过窄 `GoldenWave Adapter` 将已确认 Patch 转成受支持的 Contract 版本。
- 声明支持的 Contract 版本，并保存对应的输出 fixture 和兼容测试。
- 写入前验证目标 Inbox 和 envelope；未知主版本、无效目标或不兼容 Schema 必须 fail closed。
- 记录写入状态、幂等重试和 Project Event，不把“生成完成”伪装成“已进入 Knowledge Base”。

### 2.3 用户 Knowledge Base

用户 Knowledge Base 负责保存真实数据和 Git 历史。Malow 只通过用户明确选择的 Inbox 路径写入已确认的 Patch envelope；该 envelope 仍是 L3 待处理输入，不因 Malow Review 或 validator 成功自动成为 L1/L2/L4 正式内容。GoldenWave source repository 只提供标准、模板和工具。任一源码项目都不得自动接管用户 Knowledge Base 的 commit、push 或远端同步。

## 3. Contract 交付物

首个正式版本计划使用独立语义版本，例如 `knowledge-patch/v0.1.0`，并在 GoldenWave 仓库中提供：

```text
contracts/knowledge-patch/v0/
  schema.json
  examples/
    valid/
    invalid/
  CHANGELOG.md
  validator/
```

Envelope 必须带显式 `contract_version`。首版 Schema 应覆盖 Malow 当前已经写入的稳定 Patch ID、`idempotency_key`、目标层、可选目标位置、来源 Project / Matter / message refs、Patch 类型、内容、证据与关系字段、确认时间。

目录是计划中的协议交付边界；在 Schema、示例和 validator 实际进入仓库并通过验收前，不得把 Contract 标记为已发布。

## 4. 版本与兼容

- `PATCH`：修正文档、示例或不改变合法输入集合的 validator 缺陷。
- `MINOR`：仅增加可选字段、枚举能力或向后兼容规则。
- `MAJOR`：删除或重命名字段、改变既有字段语义、收紧既有合法输入，或改变回执与幂等行为。
- Producer 必须写入完整 `contract_version`；Consumer 和 validator 必须明确列出支持范围。
- 未知主版本默认拒绝，不猜测、不静默丢字段、不自动改写为旧版本。
- 兼容迁移应提供旧版与新版 fixture；需要数据迁移时，迁移器与回滚说明随 Contract 发布。

## 5. 同步迭代流程

跨仓库变更按以下顺序进行：

1. 在 GoldenWave 先修改 Contract、测试向量和兼容说明。
2. GoldenWave 完成 validator 自测并发布可固定引用的 tag 或 release artifact。
3. Malow 更新 Adapter、支持版本声明、fixture 和迁移逻辑。
4. 契约测试执行 `Malow output -> GoldenWave validator`，同时覆盖合法、非法、重复写入和未知版本。
5. 两个仓库分别提交、发布和回滚；不要求同一 commit、同一 tag 或锁步发版。

若 Contract 与 Malow 需要并行设计，可以先在 GoldenWave PR 中确定候选 Schema，Malow 使用该 PR 的测试向量验证；正式合并时仍遵守“GoldenWave 先发布、Malow 后固定版本”的顺序。

## 6. 当前迁移状态

- 关系与所有权：已定。
- Git submodule：明确不采用。
- Malow 当前 `knowledge-patches.jsonl` envelope：已实现，但尚未携带正式 `contract_version`。
- GoldenWave 正式 Schema、validator 与回执协议：待实现。
- 下一兼容节点：GoldenWave 发布 `knowledge-patch/v0.1.0`，随后 Malow 迁移当前 envelope 并建立跨仓库契约测试。

## 7. 接口优先级

- GoldenWave 优先 CLI 化：`goldenwave init / validate / ingest / doctor` 是 Contract、摄入和本地环境诊断的首要执行面。
- GoldenWave MCP 在 CLI、validator 和权限边界稳定后进入；先只读正式知识，再允许提交 Inbox 候选，不直接 inject。
- Malow 优先 MCP 集成化：外部 Agent 通过 Project-scoped resource 和受控 import / draft tool 接入 Project Memory。
- Malow CLI 保持为窄 `malowctl doctor / import / serve-mcp`，不复制 Desktop 的对话、来源和 Review 体验。
- CLI、MCP、Desktop 和 Skill 必须复用各自项目的同一核心服务与 Contract，不以不同接口维护多套领域规则。

## 8. 非目标

- 不把 GoldenWave 内部目录结构复制到 Malow 领域模型。
- 不把 Malow 应用源码放入 GoldenWave Knowledge Base。
- 不把用户的个人 Knowledge Base 提交到 GoldenWave 或 Malow 源码仓库。
- 不用 submodule 指针代替 Contract 版本。
- 不因协议关联引入自动 Git commit、push 或双向数据同步。
