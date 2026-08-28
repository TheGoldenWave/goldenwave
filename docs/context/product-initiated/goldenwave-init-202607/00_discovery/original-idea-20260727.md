---
req_id: goldenwave-init-202607
source: product-initiated
status: captured
created: 2026-07-27
---

# GoldenWave Init Skill 原始设想

## 用户原始需求

> 这个项目带初始化能力么，我希望可以通过一个 init Skill 让用户快速实现当前项目的初始化（不全依赖 LLM，适当使用脚本），你看看怎么设计方案。

## 已确认方向

- 面向 GoldenWave 最终用户初始化个人 Knowledge Base，而不是初始化 GoldenWave 源码仓的 Agentic Engineering 开发底座。
- 以 `goldenwave-init` Skill 作为自然语言入口，但文件生成、冲突检测、安全门禁和验证由确定性脚本完成。
- 先交付新建空库的可靠 MVP，再扩展已有库的 `adopt` 和版本升级能力。
- 初始化过程本地优先，不自动配置 Git remote，不自动 push，不把个人信息交给远程服务。

## 现状观察

仓库已有 `skills/goldenwave-init/SKILL.md` 与 `scripts/init.sh`，能够生成部分 v0.1 目录，但 Skill 脱离源码仓后无法可靠定位脚本，生成物也未覆盖当前 SPEC 的 `.private/`、隐私 ignore、`agent-contract.md`、schema、manifest 和 doctor 门禁。因此现有能力应定义为原型，而不是可交付初始化产品。
