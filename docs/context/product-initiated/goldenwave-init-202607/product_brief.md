---
req_id: goldenwave-init-202607
source: product-initiated
status: approved-for-prd
owner: GoldenWave
updated: 2026-07-27
---

# 产品简报 — GoldenWave Init Skill

## 发现来源

GoldenWave 已有 v0.1 初始化脚本和 Skill，但首次使用仍要求用户克隆源码、理解目录、手动执行脚本、初始化 Git 并自行判断初始化是否安全。随着 SPEC 引入 `git_tracked / local_private / ephemeral`，仅生成目录已不足以建立可信的 Knowledge Base。

## 核心假设

我们相信，将自然语言 Skill 入口与确定性初始化脚本结合，可以让目标用户在不理解 GoldenWave 内部结构的前提下，快速创建一个符合 SPEC、可重复验证且默认不泄露私有数据的个人库。

验证方式是：在干净环境和真实路径上重复执行初始化与 doctor，测量首次可信初始化时间、幂等性、冲突处理和 Git 隐私门禁结果。

## 功能概要

用户通过“初始化 GoldenWave”触发 Skill。Skill 只收集目标路径和少量必要选择，随后调用自包含脚本执行 `plan -> apply -> doctor`。脚本生成标准目录、Agent 入口、manifest 和安全 ignore；可选初始化本地 Git，但不会自动 commit、配置 remote 或 push。成功后再进入独立的 Profile onboarding。

## 预期效果

| 指标 | 当前值 | MVP 目标值 | 衡量方式 |
|------|-------|-----------|---------|
| Time to First Governed Value | 需克隆仓库和手动操作，未基线化 | 新建空库 <= 5 分钟 | 从触发 Skill 到 doctor 通过 |
| 幂等性 | 无自动验证 | 同版本重复执行零非预期 diff | 临时目录重复执行测试 |
| 私有数据 Git 误跟踪 | 缺少门禁 | 0 | `git check-ignore` 与 `git ls-files` 验收 |
| 冲突静默覆盖 | 当前跳过但不形成计划 | 0 | 非空目录与冲突 fixture |
| 跨平台 | Bash 为主 | macOS/Linux/Windows 支持矩阵内通过 | 干净环境验收 |

## 风险与依赖

- 初始化模板必须跟随 SPEC 演进，不能复制出第二套规范。
- `doctor` 未通过前不得执行首次 commit。
- `adopt` 涉及已有用户文件和迁移风险，不进入新建 MVP 的自动写入路径。
- Python 运行时支持范围需要在实施前冻结；脚本使用标准库，避免安装第三方依赖。
- 本功能属于 Phase 1 Trustable Core，需与未来统一 `goldenwave` CLI 复用同一初始化与验证内核。

## 关联文档

- 原始设想：`00_discovery/original-idea-20260727.md`
- PRD：`../../../prd/goldenwave-init/PRD.md`
- 技术设计：`../../technical/goldenwave-init/init-skill-design.md`
