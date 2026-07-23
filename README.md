# 🌊 goldenwave

![version](https://img.shields.io/badge/version-0.1-blue) ![license](https://img.shields.io/badge/license-MIT-green) ![status](https://img.shields.io/badge/status-early%20alpha-orange) ![local-first](https://img.shields.io/badge/local--first-%E2%9C%93-success) ![format](https://img.shields.io/badge/format-Markdown%20%2B%20git-lightgrey)

> A **local-first, plain-Markdown, git-auditable** personal AI operating system —
> an open **SPEC + Skill suite** that keeps your **knowledge, facts, and persona**
> cleanly layered, governed, and readable by any agent.

**中文**：一个本地优先、纯 Markdown、git 可审计的个人 AI 操作系统的**开放标准 + Skill 套件**。把「知识 / 事实 / 人格」三类自我数据干净分层、受治理地统一，任何 Agent（Claude Code / Codex / Cursor / Hermes）都能读写。

---

## Why goldenwave

现有方案各缺一角：

| 项目 | 做了什么 | 缺什么 |
|---|---|---|
| Pieces | 被动捕获 + 长期记忆 | 黑盒、无结构、无沉淀 |
| OpenHuman | 全栈个人 agent | 托管后端、黑盒记忆、不可审计 |
| nuwa / yourself / immortal | 人格蒸馏 | 无结构化事实、无知识库 |
| **goldenwave** | **三维分层 + 受治理工作流 + 可审计** | —— |

**核心差异**：别人是黑盒记忆，goldenwave **一切皆 markdown + git，全可 diff、全可审计**。

---

## 五层架构

| 层 | 职责 | 载体 |
|---|---|---|
| **L1 Profile** | 管事实（含人格描述） | `profile/` 9 域 + `persona/` |
| **L2 Knowledge** | 管沉淀 | `wiki/` 8 类页面（Karpathy 式互链） |
| **L3 Workflow** | 管流转 | 摄入 / 路由 / 同步 |
| **L4 Project** | 管执行 | 项目目录 + 可运行 Skill（含人格实例） |
| **L5 Git** | 管审计 | git 版本 / 回滚 / 跨设备同步 |

详见 [SPEC.md](SPEC.md)。

---

## Quick start

```bash
git clone git@github.com:TheGoldenWave/goldenwave.git
cd goldenwave
bash scripts/init.sh ~/MyKnowledgeBase
```

然后把 `skills/` 下的 Skill 挂到你的 agent（Claude Code `.claude/skills/` 等），即可开始用 agent 维护你的个人库。

---

## Integrations

- [Malow](docs/malow-integration.md)：Malow 作为下游 Knowledge Patch producer，通过版本化 GoldenWave Contract 和运行时 Inbox 路径接入；两个源码仓库保持独立，不使用 Git submodule。

---

## 项目状态

**v0.1（当前）**：开放标准 + 结构骨架 + init 脚本 + 三个 Skill。
路线图见 [ROADMAP.md](ROADMAP.md)。

## License

[MIT](LICENSE) © 2026 GoldenWave
