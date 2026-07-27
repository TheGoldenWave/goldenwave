---
feature_id: goldenwave-strategy
document: knowledgebase-inventory
status: review
observed_at: 2026-07-25
source_root: /Users/goldenwave/KnowledgeBase
sensitivity: low-metadata-only
source_commit: ba8b8cf977237830b8dc21cd12e0579c09849029
dirty_status_sha256: e02a3a52fedd5c6550559c79c65bf1dc9f4b73701adb3ced3ef27756ce20f7fd
tracked_diff_sha256: f30cc5998f3725968f2d286081d3c08008f970f786fb12872efe46e996c2d799
worktree_content_sha256: acc30da933e29960735534704fe1caee13c060d191a4dfa280afeb500fcde6a8
---

# KnowledgeBase 低敏盘点

## 1. 范围与方法

本盘点是 GoldenWave Phase 0 的 P0-03 输入，目的不是审计个人内容，而是确认真实旧库的结构、Agent 接入、Git 边界和 `adopt/doctor` 所需兼容面。

只读取：

- 目录、文件数量、索引和 Schema；
- `AGENTS.md`、维护说明、Profile 控制台合约；
- frontmatter 中的 `sensitivity`、`maintainer` 与 Git 跟踪状态；
- `.gitignore`、Git 状态、维护脚本和自动化摘要。

明确未读取：

- `.private/` 正文（实际目录不存在）；
- 财务、健康、亲友或其他 L3 事实正文；
- `profile/persona/voice-samples.md` 正文；
- 原始来源文件正文、凭据与远端地址。

本报告不复制个人正文，只记录数量、类型、边界缺口和脱敏路径类别。

### 快照与可复跑口径

- 基准提交：`ba8b8cf977237830b8dc21cd12e0579c09849029`；
- 盘点时工作树：4 个已修改维护报告/仪表盘文件、1 个未跟踪 inbox 文件；porcelain 状态 SHA-256 为 `e02a3a52...`，tracked binary diff SHA-256 为 `f30cc599...`，tracked diff 与排序后的 untracked `path + git hash-object` 合并内容快照 SHA-256 为 `acc30da9...`；
- 内容页：`wiki/*/*.md` 且文件名不是 `index.md`；
- 类型索引：8 个 `wiki/<type>/index.md`；总索引：`wiki/index.md`；
- Profile sensitivity：只扫描 `git ls-files profile` 返回文件的**首段 YAML frontmatter**，不扫描正文或 Schema 代码块；
- 数量与风险结论只对上述 commit + `worktree_content_sha256` 快照负责。持续自动化产生的新变更不静默并入本报告。

以下命令可直接复算关键聚合值。设置 `KB=/Users/goldenwave/KnowledgeBase` 后执行：

```bash
git -C "$KB" rev-parse HEAD
git -C "$KB" status --porcelain=v1 | shasum -a 256
git -C "$KB" diff --binary HEAD | shasum -a 256
{ git -C "$KB" diff --binary HEAD; git -C "$KB" ls-files --others --exclude-standard -z | sort -z | while IFS= read -r -d '' f; do h=$(git -C "$KB" hash-object "$f"); printf '%s\0%s\0' "$f" "$h"; done; } | shasum -a 256

find "$KB/wiki" -maxdepth 2 -type f -name '*.md' ! -name 'index.md' | wc -l
find "$KB/wiki" -maxdepth 2 -type f -name 'index.md' | wc -l
find "$KB/wiki" -maxdepth 2 -type f -name '*.md' -print0 | xargs -0 wc -cw | tail -1

for area in wiki profile .kb .sources inbox daily notes archive; do
  printf '%s ' "$area"
  git -C "$KB" ls-files "$area/**" | wc -l
done

for f in $(git -C "$KB" ls-files 'profile/*.md' 'profile/**/*.md'); do
  awk 'NR==1 && $0=="---" {fm=1; next} fm && $0=="---" {exit} fm && /^sensitivity:[[:space:]]*/ {sub(/^sensitivity:[[:space:]]*/,""); print; exit}' "$KB/$f"
done | sort | uniq -c

for p in .private .private/example profile/persona/voice-samples.md inbox/example.txt .sources/example.txt; do
  git -C "$KB" check-ignore -v "$p" || printf '%s|NOT_IGNORED\n' "$p"
done
```

## 2. 结构快照

| 区域 | 观察值 | Git 跟踪 | 语义角色 |
|---|---:|---:|---|
| `wiki/` | 197 个内容页、8 个类型索引、1 个总索引，共 206 个文件 | 206 | L2 结构化知识 |
| `profile/` | 25 个 Markdown 文件 | 25 | L1 事实与人格描述 |
| `.sources/` | 164 个来源文件，约 6.3 MB | 164 | 原始来源/证据，不进主图谱 |
| `.kb/` | 131 个维护资产，约 1.3 MB | 128 | 脚本、模板、报告、仪表盘 |
| `inbox/` | 3 个文件，其中 2 个被 Git 跟踪 | 2 | 待处理原料 |
| `daily/` | 1 个 Markdown | 1 | 人类临时记录 |
| `notes/` | 2 个文件 | 2 | 人类自由笔记 |
| `archive/` | 5 个文件 | 3 | 归档内容 |
| `.private/` | 不存在 | 0 | 目标 `local_private` 存储区尚未落地 |

Wiki 内容页分布：entities 54、concepts 50、methods 38、guides 5、projects 4、syntheses 40、comparisons 1、insights 5。

Profile 存在标记为 L1/L2 的文件，身体健康、财务、社交等目录主要仍为空索引。按 tracked 文件首段 frontmatter 统计，L1 8 个、L2 8 个、L3 5 个，另有 4 个无 `sensitivity` 的规范/索引文件；5 个 L3 是 4 个域索引和 1 个人格语料文件，不能等同于 5 份高敏实值。

## 3. Agent 与自动化接入

| 接入 | 当前观察 | 对 GoldenWave 的含义 |
|---|---|---|
| Codex / Claude | 根 `AGENTS.md` 为统一入口，声明可由任意 AI Agent 维护 | `doctor` 需要检查入口存在与约定版本 |
| Hermes | 每日维护、Git 同步、Dashboard、周度语义治理等定时任务处于运行状态 | `adopt` 不能破坏现有自动化或静默改写脚本 |
| Multica | 承接摄入、巡检、索引和术语任务；仪表盘显示历史队列积压 | Candidate 与任务状态必须区分，不能把 Issue 当正式知识 |
| Obsidian | 作为浏览层，`.obsidian/` 工作区文件被忽略 | GoldenWave 不应依赖编辑器私有状态完成核心治理 |
| 确定性脚本 | 已有 index、audit、inbox digest、candidate matcher、dashboard 等脚本 | Phase 1 应复用可验证能力，避免复制领域逻辑 |

知识库采用本地 SSD 为权威、Git 远端为备份与跨设备分发。当前分支为 `main`，最近提交日期为 2026-07-24。盘点时存在由自动化生成的未提交报告变更；本任务未修改或清理这些变更。

## 4. 已观察的边界缺口

### R1 — `local_private` 物理边界尚不存在（High）

- `.private/` 不存在；
- `.gitignore` 未排除 `.private/`；
- `git check-ignore` 对 `.private/` 和示例子路径均返回未忽略。

影响：当前真实库不能满足 GoldenWave SPEC 对 `local_private` 的 fail-closed 承诺。Phase 1 的 `doctor` 必须把它判定为不安全，而不是自动声称已保护。

### R2 — Profile 规则与 Phase 1 远程模型策略冲突（High）

现有 `profile/console/agent-contract.md` 声明 L2/L3 对云端 API 当前放行；已批准的 GoldenWave Phase 1 约束是 `remote_model` 默认拒绝。

影响：`adopt/doctor` 需要报告 policy drift，并区分“旧库当前行为”与“GoldenWave 推荐策略”。在用户确认前不应静默重写个人合约。

### R3 — Git 中存在标记为 L3 的 Profile 文件（High）

Git 跟踪的 Profile 中有 5 个 `sensitivity: L3` 文件，其中 4 个是域索引，另有 1 个人格语料文件。盘点未读取正文，无法仅凭 frontmatter 判断是否包含必须硬删除的实值。

影响：`doctor` 应报告 `sensitivity x storage_class x tracked` 组合风险，并要求人工复核；不能把 `L3` 自动等同于泄露，也不能忽略。

### R4 — 原料和来源默认进入 Git（Medium）

`.sources/` 164 个文件全部受 Git 跟踪，`inbox/` 也有 2 个被跟踪；根 `.gitignore` 未排除这两个目录。

影响：知识库约定中的“原料/证据区”并不等同于 `ephemeral`。Contract 必须显式携带 storage class，不能通过目录名推断删除或同步语义。

### R5 — 规范与存量质量存在渐进差异（Medium 兼容风险 / Advisory 诊断）

最新确定性巡检显示：197 个 Wiki 内容页无 frontmatter/YAML/断链错误，但有 85 个缺少 `description`、61 个 `related` 异常、35 个孤立页和历史标签漂移。

影响：它对 adopt 兼容设计是 Medium 风险，但对单次 `doctor` 结果只应标为 Advisory。`adopt/doctor` 需要把问题分为 `unsafe / invalid / repairable / advisory`，存量质量问题不应与隐私红线混为同一失败级别，否则真实旧库永远无法采用。

### R6 — 自动化与人工状态并存（Medium）

知识库有多个定时任务、自动生成报告和 Multica 队列；盘点时工作区非干净。

影响：事务与 CAS 设计必须考虑外部进程并发，`doctor` 需明确只读检查和修复操作的不同权限，不能假设单进程、干净工作树。

### R7 — 文档规模元数据已经漂移（Low）

`AGENTS.md` 中的旧规模描述约 47 页/30 个来源，实际已达到 197 内容页/164 个来源。

影响：规模数据应由脚本生成，不作为手工兼容合同；这也是 Context Pack 必须渐进检索、不能全库注入的现实依据。

## 5. 对 Phase 0/1 的直接输入

### Threat Model 必须覆盖

- Git 远端、自动同步和历史不可删除边界；
- 本地权威库、Hermes cron、Multica 与多个 Agent 的并发写入；
- L3 frontmatter 与实际 storage class 不一致；
- `.private/` 缺失、ignore 绕过、符号链接和路径穿越；
- 原料、来源、日志、文件名与错误消息的旁路泄露；
- 旧 Agent Contract 与新 Policy 的漂移检测；
- 自动修复、人工确认和只读诊断的权限分离。

### 给黄金任务集的候选输入

- 对真实旧库执行只读 `doctor`，正确输出 `unsafe/invalid/repairable/advisory` 诊断级别，并可另附 High/Medium/Low 风险优先级；
- 识别 `.private/` 缺失和 Git ignore 缺口；
- 识别 tracked L3，但不读取或输出正文；
- 识别远程模型 policy drift，不静默改文件；
- 将 Wiki 质量问题标为 repairable/advisory，而非安全泄露；
- 在 dirty worktree 和外部自动化存在时保持只读、可重复；
- 对 197 个内容页、206 个 Wiki Markdown（约 1.03 MB，`wc -w` 为 65,800）的检索策略设容量预算，并用测试证明全库注入超过该预算；具体 token 预算、fixture 快照、错误码和判级 rubric 由 P0-05 冻结。

本节只提供从真实库抽取的 doctor/adopt 场景，不是完整 P0-05 Oracle。P0-05 仍必须补齐 Profile / Knowledge / Project 三类任务、不可变 fixture 快照、期望错误码、严重度 rubric 和可测容量阈值。

### `adopt/doctor` 兼容级别建议

| 级别 | 含义 | 当前真实库示例 |
|---|---|---|
| `unsafe` | 违反信任边界，必须 fail closed | `.private/` 未 ignore、潜在 tracked L3 需复核 |
| `invalid` | Contract 或结构不可解析 | 当前未观察到 frontmatter/YAML 解析失败 |
| `repairable` | 可生成显式修复计划，不自动执行 | policy drift、目录/索引约定差异 |
| `advisory` | 不阻断采用的质量提示 | description、related、孤立页、规模描述漂移 |

诊断级别判定规则：违反数据边界或可能产生未授权持久化为 `unsafe`；结构/Contract 无法解析为 `invalid`；可生成显式且可逆修复计划为 `repairable`；不影响信任边界与解析的质量问题为 `advisory`。产品规划中的 High/Medium/Low 表示风险优先级，不与这四个运行时诊断级别互换。

## 6. 未知项

- Git 远端是否公开、历史中是否曾出现必须 purge 的内容；本盘点未访问远端权限或历史正文；
- 自动化进程的精确并发和锁机制；
- L3 文件正文是否需要迁移到 `local_private`；
- 备份、导出和其他设备副本的保留周期；
- 个人用户可接受的 Candidate review 摩擦。

这些未知项应由 Threat Model 和后续用户/设计伙伴验证处理，不能在 P0-03 中推断。

## 7. 结论

真实 KnowledgeBase 足以作为 GoldenWave 的有效 dogfooding 样本：它具有 197 个结构化知识页、Profile、来源库、多个 Agent 和持续自动化，同时保留明显的旧库策略漂移。Phase 1 的第一价值不是再初始化一个空库，而是能够在不读取敏感正文、不破坏现有工作流的前提下，准确指出哪些状态不安全、哪些可修复、哪些只是建议。

P0-03 未发现需要立即修改个人 KnowledgeBase 的授权内动作；所有修复应先进入 Threat Model、ADR 和失败验收测试。
