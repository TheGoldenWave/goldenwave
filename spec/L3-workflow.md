# L3 — Workflow 规范（流转层）

> 连接各层的"动词"：数据怎么进、怎么分流、怎么同步。

## v0.1 范围
- **init**：一键生成 L1+L2+L5 骨架（见 scripts/init.sh）。
- **手动摄入**：用户把原料丢进 `inbox/`，由 agent 按 L1/L2 规范归类沉淀。
- **研究归档约定**：外部产出的调研 md 默认归档进 `.sources/research-reports/`，洞察沉淀进 `wiki/`。
- **同步**：见 L5。

## v0.2 预留 — 半自动摄入路由器（本版不实现）
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
