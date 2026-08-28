# L3 — Workflow 规范（流转层）

> 连接各层的"动词"：数据怎么进、怎么分流、怎么同步。

本层正式中文名为知识治理工作流（Knowledge Governance Workflow）。它负责候选内容的 capture、route、score、redact、render、confirm、inject 和 sync，不等同于 Malow 等执行系统中的项目工作流（Project Workflow）。Project Workflow 可以产出候选，但候选仍需经过本层治理后才能进入 GoldenWave 正式层。

## v0.1 范围
- **init**：一键生成 L1+L2+L5 骨架（见 scripts/init.sh）。
- **手动摄入**：用户把原料丢进 `inbox/`，由 agent 按 L1/L2 规范归类沉淀。
- **研究归档约定**：外部产出的调研 md 默认归档进 `.sources/research-reports/`，洞察沉淀进 `wiki/`。
- **同步**：见 L5。

## v0.2 进行中 — 半自动摄入路由器

`goldenwave-ingest` Skill 与 `_pending/` 约定已经进入仓库；版本化 Contract、统一 `goldenwave` CLI 和可执行 validator 尚未完成，因此 v0.2 仍处于进行中，不能标记为完整发布。

摄入流水线：
1. **capture**：inbox / 被动 connector 收集原料
2. **route**：判断 → 事实(L1) / 知识(L2) / 人格(persona) / Social Memory 对象或边
3. **score**：计算稳定度、证据等级、敏感度、policy tags 与存储等级
4. **merge-check**：涉及 Person/Collective 时只生成身份合并候选，不静默合并
5. **consent-check**：按 store/summarize/suggest/share/remote_model 分别校验授权
6. **redact**：删除超出用途的字段，隔离原始材料和日志中的高敏内容
7. **render**：按目标层的 frontmatter 与 storage_class 渲染候选
8. **user-confirm**：高敏、第三方、推断、合并与对外用途必须由用户确认
9. **inject**：原子写入对象、边和索引并留痕；失败时不得留下悬空引用

`merge-check/consent-check/redact` 对不涉及第三方身份的数据可简化，但不得跳过敏感度与存储等级判断。

## Social Memory 路由

- “我与某人/组织是什么关系” → L1 `relationship`。
- “某人属于某组织/团队” → L1 `affiliation`，前提是该信息与用户关系维护有关。
- “我们发生了一次有意义的联系” → L1 `interaction`。
- “我答应或决定跟进什么” → L1 `commitment`。
- 公开人物或组织的可复用知识 → L2 `entity`，不得与 L1 私人关系记录混写。
- 会面准备、节日联系、季度关系回顾等目标型执行 → L4 Project。

所有 Social Memory 候选默认进入 `inbox/_pending/social/`。第三方高敏内容、推断、身份合并、远程模型处理和外部分享不存在自动直写路径。

## 摄入红线
- 路由不确定时 → 进草稿 / 问用户，不静默入库。
- 公司/团队的通用知识不进 L1；公司、团队可作为与用户有关的 Collective 进入 Social Memory。
- 原始全文按用途进入 `.sources/`、`local_private` 或 `ephemeral`；第三方原始聊天默认 ephemeral，不能因摄入而自动进入 Git。
- Social Memory 推断只可作为候选，不能在用户确认时丢失 `inference` 证据标记。
- 对外 producer 不因 Contract 校验成功获得 share、remote_model、commit 或 push 权限。

## 外部 producer 合同

外部应用可以向 `inbox/` 生成受治理候选，但不能依赖 GoldenWave 源码仓库的瞬时目录实现。接入必须遵守版本化 Contract：

- GoldenWave 定义 Schema、示例、validator、幂等和兼容规则。
- producer 写入显式 `contract_version`，并在写入前通过对应 validator。
- 未知主版本、低置信度、高敏或冲突候选 fail closed，进入待确认路径或返回明确错误。
- 用户 Knowledge Base 保持独立 Git 历史；协议接入不授权外部应用自动 commit 或 push。
- Contract 校验和 Inbox 接收只证明 envelope 可处理，不表示内容已经进入 L1/L2/L4；正式沉淀仍经过 route、score、render、用户确认与 inject。
- Social Memory producer 还必须通过 merge、consent、redact 和 revocation 测试；未知身份与未知授权默认拒绝。

Malow 是首个计划接入的 Knowledge Patch producer，仓库关系、同步迭代顺序和当前迁移状态见 [GoldenWave 与 Malow 集成合同](../docs/malow-integration.md)。该关系不改变“标准写进库，不绑定单一工具”的设计原则。
