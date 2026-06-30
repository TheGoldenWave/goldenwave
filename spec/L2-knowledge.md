# L2 — Knowledge 规范（知识层）

> 存「可复用、可迁移的知识」。遵循 Karpathy 式 LLM-Maintained Wiki：持久互链 markdown，非 RAG。

## 目录
```
wiki/
├── index.md                # 结构化知识总览
├── concepts/ entities/ methods/ guides/
├── projects/ syntheses/ comparisons/ insights/
│   └── 各 type/index.md     # 目录级索引（脚本按 frontmatter 生成）
INDEX.md  kb-schema.md  glossary.md
```

## 八类页面（type 枚举）
entity / concept / method / guide / project / synthesis / comparison / insight

## Frontmatter（必填）
```yaml
---
id:          # 英文 kebab-case，全库唯一，不随文件名变
title:       # 中文为主
description: # 一句话摘要
type:        # 八类之一
tags:        # 中文两层 一级/二级，1-4 个
related: []  # 目标页面 id 列表
created:  updated:  status:   # draft/active/stale/archived
source:      # 可选
---
```

## 命名规范
- 文件名：中文核心标题（不含括号注释）
- id：英文 kebab-case（related/程序引用的稳定锚点）
- wikilink：指向中文文件名 `[[中文文件名|显示名]]`

## Karpathy 四操作
- **ingest**：读源 → 列出会 touch 的页面集合 → 跨页更新 + INDEX + log
- **query**：INDEX-first（先读索引+description，不够再读正文），好答案 file back 成新页
- **lint**：矛盾/陈旧/孤儿/缺页/缺交叉引用/数据缺口 六查
- **index & log**：INDEX.md 内容索引 + .kb/log.md 时间轴（事件类型受控）

## 质量标准
最低 ~200 字；每页 ≥1 入站 + ≥1 出站链接；90 天未更新触发陈旧审查。
