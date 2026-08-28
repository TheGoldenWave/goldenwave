# 🌊 goldenwave

![version](https://img.shields.io/badge/version-0.1-blue) ![license](https://img.shields.io/badge/license-MIT-green) ![status](https://img.shields.io/badge/status-early%20alpha-orange) ![local-first](https://img.shields.io/badge/local--first-%E2%9C%93-success) ![format](https://img.shields.io/badge/format-Markdown%20%2B%20git-lightgrey)

> A **local-first, auditable Personal AI Context Governance Layer** —
> turning facts, knowledge, and reusable experience into user-owned context that can be
> safely used by different agents.

**中文**：一个本地优先、可审计的**个人 AI 上下文治理层**。它把事实、知识和可复用经验转化为用户拥有、受治理、可被 Claude Code、Codex、Cursor、Hermes 等不同 Agent 安全使用的长期资产。

**一句话介绍**：一份由用户拥有的上下文，治理一次，供不同 Agent 使用。

---

## GoldenWave 是什么

GoldenWave 不是单个 Skill，也不负责运行或编排 Agent。它的目标运行模型由四个内核组成：

| 内核 | 作用 | 当前状态 |
|---|---|---|
| **Store** | 表达和保存 Profile、Knowledge、来源与存储等级 | 已有规范和 Markdown 骨架 |
| **Govern** | 将写入变成 Candidate，并执行验证、确认、审计和撤回 | 部分 Skill；CLI/Validator 待实现 |
| **Serve** | 为具体任务生成最小、带来源和权限的 Context Pack | 待验证 |
| **Learn** | 从 Agent Run 提取可晋升的事实、知识和经验候选 | 待验证 |

仓库中的 `.agents/`、`.claude/` 和 `.codex/` 是维护本项目所使用的 **Agentic Engineering harness**，属于开发协作基础设施，不是 GoldenWave 的产品定义，也不会作为最终用户安装包的运行依赖。用户产品边界是规范、CLI/脚本、Skills、模板和必要适配器。

“个人 AI 操作系统”是长期愿景；当前产品类别是 **Personal AI Context Governance Layer**。仓库虽已按 MIT 协议公开，但 Contract 和 API 仍为 `experimental`，不承诺公共兼容性或生产可用。

---

## Why goldenwave

现有方案各缺一角：

| 项目 | 做了什么 | 缺什么 |
|---|---|---|
| Pieces | 被动捕获 + 长期记忆 | 黑盒、无结构、无沉淀 |
| OpenHuman | 全栈个人 agent | 托管后端、黑盒记忆、不可审计 |
| nuwa / yourself / immortal | 人格蒸馏 | 无结构化事实、无知识库 |
| **GoldenWave** | **结构化上下文 + Candidate 治理 + 跨 Agent 可移植性** | 当前仍缺运行闭环与外部验证 |

**核心差异**：GoldenWave 不把长期上下文锁在黑盒记忆中。允许长期保留的资产使用 Markdown + Git；需要保证撤回的第三方数据保存在本地私有层；摄入协议和中间数据保持文本化、可验证、可治理。

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

## 验证路径

GoldenWave 采用“个人验证后正式发布”的路径：先在真实 KnowledgeBase 中完成闭环，再从被验证的实践提炼公共产品。

近期黄金路径：

1. 接入真实 KnowledgeBase 并通过 `doctor`；
2. 为真实任务生成 Context Pack；
3. Claude Code 与 Codex 消费同一 Contract；
4. Agent 提交 Candidate，用户 review/accept/reject；
5. 新上下文在后续任务中被正确复用。

完整定位、优劣势、指标和阶段 Gate 见[产品战略与迭代规划](docs/prd/goldenwave-strategy/PRD.md)。Social Memory 已完成的设计继续保留，但实施延后为领域验证候选。

---

## Quick start

Phase 1A 的安全初始化器已提供 `plan / apply / doctor` 三步闭环。默认不联网、不配置 remote、不自动 commit，也不会猜测个人事实。

```bash
git clone git@github.com:TheGoldenWave/goldenwave.git
cd goldenwave
python3.11 skills/goldenwave-init/scripts/goldenwave_init.py plan \
  --target ~/MyKnowledgeBase \
  --mode new \
  --format json

python3.11 skills/goldenwave-init/scripts/goldenwave_init.py apply \
  --target ~/MyKnowledgeBase \
  --mode new \
  --git off \
  --format json

python3.11 skills/goldenwave-init/scripts/goldenwave_init.py doctor \
  --target ~/MyKnowledgeBase \
  --format json
```

兼容入口仍保留：

```bash
bash scripts/init.sh ~/MyKnowledgeBase
```

确认 `doctor` 通过后，再把 `skills/` 下的 Skill 挂到你的 agent，并开始填写 `profile/console/me.md`。

---

## Integrations

- [LifeSub、Malow 与 GoldenWave](docs/lifesub-malow-integration.md)：LifeSub 作为声音与情境证据系统，Malow 作为项目处理与人工审核层，GoldenWave 作为长期上下文治理系统；三者通过 Evidence Contract 与 Knowledge Patch Contract 解耦。
- [Malow](docs/malow-integration.md)：Malow 作为下游 Knowledge Patch producer，通过版本化 GoldenWave Contract 和运行时 Inbox 路径接入；两个源码仓库保持独立，不使用 Git submodule。
- [Malow 能力与 Workflow 集成](docs/malow-capability-workflow-integration.md)：区分 Malow Project Workflow 与 GoldenWave Knowledge Governance Workflow，并定义 Skill / Workflow 从 Matter 到 Project、再到全局的受治理晋升路径。
- [核心术语中英对照](docs/core-terminology.md)：统一 Profile、Knowledge、Skill、Capability 与两类 Workflow 的中英文领域名。

---

## 项目状态

GoldenWave 当前处于 **early alpha**：

- **v0.1 已完成**：开放规范、五层结构、初始化脚本，以及知识、事实和人格维护 Skills。
- **Phase 0 内部基线已完成**：外部设计伙伴验证仍在并行等待，所有 Contract/API 均为 `experimental`。
- **Phase 1A 已完成内部 Gate**：安全 init、只读 doctor/adopt inventory 和 Git 泄露门禁已可运行。
- **近期主线**：下一步验证 Phase 1B Candidate Contract，再推进 Reliable Inject 和跨 Agent Context Pack。
- **后续方向**：只有通过阶段 Gate 后，才进入 Governed Learning、领域验证和正式开源产品发布。

当前版本适合研究、试用和共同定义标准，不应被描述为已经完成的全功能个人 AI OS。完整计划见 [ROADMAP.md](ROADMAP.md)。

## License

[MIT](LICENSE) © 2026 GoldenWave
