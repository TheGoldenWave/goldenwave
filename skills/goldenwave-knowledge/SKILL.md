---
name: goldenwave-knowledge
description: 按 Karpathy 式 LLM-Maintained Wiki 维护 goldenwave 的 L2 知识层。当用户要 ingest 资料、查知识、沉淀洞察、lint 知识库时触发。
---

# goldenwave-knowledge

维护 L2 Knowledge（见 spec/L2-knowledge.md）。

## 四操作
- **ingest <源>**：读源 → 列出会 touch 的页面 → 跨页更新 + INDEX + glossary + .kb/log.md。
- **query <问题>**：INDEX-first（先读索引+description，不够再读正文）；好答案 file back 成新页。
- **lint**：六查——矛盾/陈旧/孤儿/缺页/缺交叉引用/数据缺口。
- **index**：按 frontmatter 重建各 type/index.md。

## 规则
- 八类 type；frontmatter 必填 id/title/description/type/tags/related/created/updated/status。
- 文件名中文、id 英文 kebab-case、wikilink 指中文文件名。
- 每页 ≥1 入站 + ≥1 出站链接；≥200 字。
