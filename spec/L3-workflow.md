# L3 — Workflow 规范（流转层）

> 连接各层的"动词"：数据怎么进、怎么分流、怎么同步。

## v0.1 范围
- **init**：一键生成 L1+L2+L5 骨架（见 scripts/init.sh）。
- **手动摄入**：用户把原料丢进 `inbox/`，由 agent 按 L1/L2 规范归类沉淀。
- **研究归档约定**：外部产出的调研 md 默认归档进 `.sources/research-reports/`，洞察沉淀进 `wiki/`。
- **同步**：见 L5。

## v0.2 进行中 — 半自动摄入路由器

`goldenwave-ingest` Skill 与 `_pending/` 约定已经进入仓库；版本化 Contract、统一 `goldenwave` CLI 和可执行 validator 尚未完成，因此 v0.2 仍处于进行中，不能标记为完整发布。

摄入流水线（借 OpenHuman capture→score→render→inject）：
1. **capture**：inbox / 被动 connector 收集原料
2. **route**：agent 判断每条信息 → 事实(L1) / 知识(L2) / 人格(persona)
3. **score**：打稳定度/证据分级（verbatim > artifact > impression）
4. **render**：按目标层的 frontmatter 规范渲染
5. **inject**：写入 + 更新索引 + 留痕；高敏/低稳定先进草稿待人确认

## 摄入红线
- 路由不确定时 → 进草稿 / 问用户，不静默入库。
- 公司/团队知识不进个人库（个人库绑身份，不绑公司）。
- 全文进 `.sources/`，只有蒸馏结果进 `wiki/`（进主图谱）。

## 外部 producer 合同

外部应用可以向 `inbox/` 生成受治理候选，但不能依赖 GoldenWave 源码仓库的瞬时目录实现。接入必须遵守版本化 Contract：

- GoldenWave 定义 Schema、示例、validator、幂等和兼容规则。
- producer 写入显式 `contract_version`，并在写入前通过对应 validator。
- 未知主版本、低置信度、高敏或冲突候选 fail closed，进入待确认路径或返回明确错误。
- 用户 Knowledge Base 保持独立 Git 历史；协议接入不授权外部应用自动 commit 或 push。
- Contract 校验和 Inbox 接收只证明 envelope 可处理，不表示内容已经进入 L1/L2/L4；正式沉淀仍经过 route、score、render、用户确认与 inject。

Malow 是首个计划接入的 Knowledge Patch producer，仓库关系、同步迭代顺序和当前迁移状态见 [GoldenWave 与 Malow 集成合同](../docs/malow-integration.md)。该关系不改变“标准写进库，不绑定单一工具”的设计原则。
