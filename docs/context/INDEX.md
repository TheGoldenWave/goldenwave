# 🧠 团队知识库索引 (Knowledge Index)

> **用途**：开始任何任务前，先按分类检索本索引，避免重踩已知坑点。
> **维护**：运行 `/reflect` 自动扫描未索引的经验记录并追加到对应分类表格中。
> **格式**：每条记录为一行表格行，摘要 ≤ 60 字，详情列指向完整文档路径。

---

## 🏗️ 架构决策 (Architecture Decisions)

| 日期 | 来源 | 摘要 | 详情 |
|------|------|------|------|
| 2026-07-24 | goldenwave-strategy | 可信上下文治理层，先个人闭环验证再正式发布 | `docs/context/product-initiated/goldenwave-strategy-202607/research_synthesis.md` |
| 2026-07-23 | social-memory | 逻辑层与存储等级分离，可撤回数据不得进入 Git | `docs/context/project/experience/social-memory-storage-boundary.md` |
| 2026-07-27 | goldenwave-init | 用户库 init 采用薄 Skill、确定性脚本与 doctor，源码 bootstrap 独立 | `docs/context/technical/goldenwave-init/init-skill-design.md` |
| 2026-07-27 | goldenwave-strategy | Phase 1 拆为 Safe Bootstrap、Candidate Contract、Reliable Inject | `docs/prd/goldenwave-strategy/amendments/2026-07-27-organization-lightening.md` |
| <!-- 示例: 2025-04-10 --> | <!-- 1.0.0-用户登录-202504 --> | <!-- 选用 PostgreSQL 而非 MongoDB，因为需要事务一致性 --> | <!-- docs/context/project/experience/db-choice.md --> |

## 🐛 Bug 模式 (Bug Patterns)

| 日期 | 来源 | 摘要 | 详情 |
|------|------|------|------|
| 2026-07-27 | goldenwave-strategy | repo scorecard 若放宽为自由字段，会泄露 `.private/` 路径与二次回答痕迹 | `docs/context/project/experience/phase0-scorecard-metadata-boundary.md` |
| 2026-07-27 | goldenwave-init | doctor 路径先过 allowlist，只读扫描限 frontmatter，Git 根需精确匹配 | `docs/context/project/experience/phase1a-doctor-boundaries.md` |
| <!-- 示例: 2025-04-12 --> | <!-- 1.0.0-并发优化-202504 --> | <!-- 并发写入导致乐观锁冲突，需 retry 机制 --> | <!-- docs/context/project/experience/optimistic-lock-retry.md --> |

## 🧩 设计模式 (Design Patterns)

| 日期 | 来源 | 摘要 | 详情 |
|------|------|------|------|
| <!-- 示例: 2025-04-11 --> | <!-- 1.0.0-用户登录-202504 --> | <!-- 统一使用 Repository 模式封装数据访问层 --> | <!-- docs/context/project/experience/repository-pattern.md --> |

## 📚 领域知识 (Domain Knowledge)

| 日期 | 来源 | 摘要 | 详情 |
|------|------|------|------|
| <!-- 示例: 2025-04-13 --> | <!-- 1.1.0-优惠券系统-202504 --> | <!-- 优惠券叠加规则：同类不叠加，异类最多叠 2 张 --> | <!-- docs/context/project/experience/coupon-rules.md --> |

## 🔧 环境与工具 (Environment & Tooling)

| 日期 | 来源 | 摘要 | 详情 |
|------|------|------|------|
| 2026-07-27 | goldenwave-strategy | YAML 校验需禁 alias/重复键，repo 证据目录只接受 allowlist metadata | `docs/context/project/experience/phase0-scorecard-metadata-boundary.md` |
| <!-- 示例: 2025-04-09 --> | <!-- infra --> | <!-- CI 环境 Node 版本必须 ≥ 18，否则 esbuild 构建失败 --> | <!-- docs/context/project/experience/ci-node-version.md --> |

---

> **给 Agent 的指示**：当你在需求开发中（如 `docs/prd/*/notes.md`）记录了坑点后，请将其提炼到 `docs/context/project/experience/` 目录下，并运行 `/reflect` 或手动更新此索引。保持摘要简洁（≤ 60 字），详情列填写完整相对路径。
