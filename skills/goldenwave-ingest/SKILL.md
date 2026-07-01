---
name: goldenwave-ingest
description: goldenwave 半自动摄入路由器。把 inbox/ 里的原料自动判断该进 事实(L1)/知识(L2)/人格(persona) 哪一层，渲染成合规页面并安全写入；不确定或敏感的先进草稿待确认。当用户说"处理 inbox / 整理收件箱 / ingest / 归类这条笔记"时触发。
---

# goldenwave-ingest（摄入路由器）

把任意原料经 capture→route→score→render→inject 五段流水线，落到 goldenwave 三维分层的合规页面。遵循 SPEC.md 与 spec/L3-workflow.md。

## 默认参数（可在对话中覆盖）
- 分类器：模型无关，用本 prompt 驱动（本地/云模型皆可）
- 置信度阈值：**0.7**（低于则进草稿）
- 形态：纯 skill（批处理 route.py 留待后续）

## 流水线

### ① capture
读取 `inbox/` 下每条原料（.md/.txt/链接/粘贴文本），提取纯文本 + 元数据 `{text, source, captured_at}`。

### ② route（核心分类）
对每条原料判定归属层，输出 `{layer, target, confidence, reason}`：
- **是"此刻为真的事实"** → L1 profile，再判九域（01-body-health … 09-career-assets）
- **是"可复用、可迁移的知识"** → L2 wiki，再判八类（concept/entity/method/guide/project/synthesis/comparison/insight）
- **是"我怎么想/怎么说话"** → profile/persona（facet: expression-dna/traits/decision-style/voice-samples）
- **无价值/临时** → 建议丢弃，不入库
- `confidence < 0.7` → 进 `inbox/_pending/`

判断依据：频繁变、查来取值→L1；读来理解、换环境仍有效→L2；表达/性格指纹→persona。

### ③ score
- 证据分级：原话=verbatim，成稿=artifact，他人转述=impression
- 稳定度：一次性 vs 长期 → 决定 refresh 周期
- 敏感度：L0–L3 → 决定是否进 git / 是否脱敏

### ④ render
套 templates/ 对应模板，生成候选页并自动填 frontmatter（id/type/tags/verified/sensitivity 等），遵循目标层 kb-schema。

### ⑤ inject
- **高稳定 + 低敏(≤L1) + 置信≥0.7** → 直接写入目标目录
- **否则** → 写 `inbox/_pending/<slug>.md`，页首附「路由决策卡」，等用户 confirm
- 写入后：更新对应 `index.md`、补双向链、追加 `.kb/log.md` 一条 `ingest` 记录

## 红线
1. 半自动：敏感(≥L2)或低置信一律进草稿，绝不静默入库。
2. 三维分流：事实/知识/人格不混淆。
3. 可审计：每次路由在 log 留 `{原料→目标, confidence, reason}`；错误可 git revert。
4. 不确定就问：拿不准归属或域，进 _pending 并列出候选让用户选。
5. 公司/团队知识不进个人库。

## 路由决策卡格式（写在 _pending 草稿页首）
```
> 🧭 路由决策｜layer=L2/concept｜confidence=0.62｜进草稿原因：置信度<0.7
> 候选：concept vs insight ；建议 tags：技术/Agent
> 确认请移至 wiki/concepts/ 并删除本卡；改判请直接编辑。
```
