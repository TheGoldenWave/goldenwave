# GoldenWave Init Skill 决策与风险记录

## 2026-07-27 — 区分用户库初始化与源码仓 bootstrap

- **决定**：`goldenwave-init` 只初始化最终用户 Knowledge Base。
- **原因**：`.agents/skills/bootstrap-agentic-project` 初始化的是 GoldenWave 维护者的研发协作底座，两者目标用户、产物和安全边界不同。

## 2026-07-27 — 薄 Skill + 确定性脚本

- **决定**：LLM 只处理意图、必要选择和结果解释；路径、模板、冲突、Git 门禁和 doctor 全部由脚本执行。
- **原因**：初始化需要幂等、可重放、跨 Agent 一致和稳定错误码，不能依赖模型每次重新生成命令或文件。

## 2026-07-27 — MVP 只承诺可靠 new

- **决定**：非空目录不再“仅补缺失文件”；MVP 的 `new` 遇到非空目标直接停止。
- **原因**：在没有 manifest、迁移规则和备份验证前，自动补文件会形成不可判定的混合版本。
- **后续**：已有库通过独立 `adopt` 只读计划和用户确认流程处理。

## 2026-07-27 — doctor 先于 Git commit

- **决定**：`.gitignore` 和 doctor 必须在 add/commit 之前通过；init 不配置 remote、不 push。
- **原因**：当前 SPEC 要求 `.private/` 不进入任何 Git 历史，一旦误提交，普通删除无法满足硬删除承诺。

## 2026-07-27 — 当前初始化能力降级为原型表述

- **决定**：在新实现通过验收前，现有 Bash 脚本与 Skill 只视为 v0.1 骨架原型。
- **原因**：当前生成物落后于 SPEC，且 Skill 脱离源码仓后无法可靠定位脚本。

## 2026-07-27 — Init 前移到 Phase 1A

- **决定**：安全 `init` 与只读 `doctor` 进入 Phase 1A Safe Bootstrap，不再等待 Candidate Contract、CAS 和事务式 inject 全部完成。
- **边界**：Phase 1A 只做新库初始化、只读诊断和 Git 泄露门禁；已有库自动修复和正式 Candidate 写入仍分别留在后续切片。

## 2026-07-27 — Doctor 必须先校验 manifest allowlist

- **现象**：若直接遍历 manifest 提供的 managed path，恶意 `../` 路径可诱导 doctor 读取 Knowledge Base 外文件。
- **规则**：只有 managed key 集与冻结 allowlist 精确一致后才允许解析或 checksum 路径；template manifest 同样先校验相对路径、重复项和完整布局。

## 2026-07-27 — 只读诊断只读取 frontmatter 与 Git 元数据

- **现象**：为识别 `storage_class: ephemeral` 而整文件读取，会扩大真实库 dogfood 的正文访问面。
- **规则**：doctor/adopt inventory 逐行读取首段 frontmatter，tracked L3 只报告相对路径与复核需要；不得输出正文、远端 URL 或库外绝对路径。

## 2026-07-27 — 嵌套目录不等于独立 Git 仓

- **现象**：仅用 `git rev-parse --is-inside-work-tree` 会把位于其他仓库下的临时测试库误判为自身 Git 仓。
- **规则**：Git 门禁只在 `--show-toplevel` 的 canonical path 与 Knowledge Base 根精确相等时启用。
