# goldenwave SPEC v0.1

> 本文件是 goldenwave 的"宪法"——定义个人 AI 操作系统的五层结构、目录布局与不可破的设计原则。
> 所有 Skill、脚本、模板都必须遵守本 SPEC。变更 SPEC 优先于变更实现。

## 0. 设计哲学

1. **本地优先**：数据存在用户机器上，云是可选增强，不是依赖。
2. **正式知识皆 Markdown + git**：进入 L1/L2/L4 的知识、事实、人格与项目资产保持纯文本，可被 `git diff`、可审计、可回滚。L3 传输 envelope、Schema 和 validator 可以使用 JSON/JSONL 等文本格式，但它们只是受治理的中间协议，不能绕过 render / confirm 直接成为正式知识。
3. **人机共读**：frontmatter 是机器协议（agent 先读它判断），正文是人机共享语义层。
4. **三维分层**：知识（可复用）/ 事实（此刻为真）/ 人格（怎么想怎么说）严格分离，互不污染。
5. **标准写进库，不绑工具**：规则存在知识库里（如 CLAUDE.md / AGENTS.md），任何遵守 SPEC 的 agent 都能接管。
6. **严格生产，宽松读取**：新建/实质修改必须合规；存量可渐进修复。

## 1. 五层架构

| 层 | 职责 | 载体 | 回答的问题 |
|---|---|---|---|
| L1 Profile | 管事实（含人格描述） | `profile/` | 关于我此刻为真的事实 |
| L2 Knowledge | 管沉淀 | `wiki/` | 世界如何运作 / 我如何思考 |
| L3 Workflow | 管流转 | 脚本 + 协议 | 数据怎么进、分流、同步 |
| L4 Project | 管执行 | 项目目录 + Skill | 为某目标做事（含人格实例） |
| L5 Git | 管审计 | git 仓 + sync | 谁/何时/改了什么/可回滚 |

各层详细规范见 `spec/L1-profile.md` … `spec/L5-git.md`，治理见 `spec/governance.md`。

## 2. 标准目录布局

```
<knowledge-base-root>/
├── CLAUDE.md / AGENTS.md   # agent 规则入口（L3 协议落地）
├── INDEX.md                # 总入口（轻量）
├── kb-schema.md            # 知识层规范（本地副本）
├── glossary.md             # 术语表
├── wiki/                   # L2 知识层（8 类页面）
│   ├── index.md
│   ├── entities/ concepts/ methods/ guides/
│   ├── projects/ syntheses/ comparisons/ insights/
├── profile/                # L1 事实层
│   ├── INDEX.md  kb-schema.md
│   ├── console/            # me.md + agent-contract.md
│   ├── 01-body-health/ ... 09-career-assets/
│   └── persona/            # 人格描述
├── projects/               # L4 执行层（可选）
├── inbox/                  # 待处理原料（L3 入口）
├── .sources/               # 来源归档（不进主图谱）
└── .kb/                    # 脚本 / 日志 / 模板
    ├── log.md  scripts/
```

## 3. 三维分层的判定口诀

- 会随时间频繁变、查来取值 → **L1 Profile**（事实）
- 读来理解、换工作仍有效 → **L2 Knowledge**（知识）
- 描述"我怎么想/怎么说话" → **L1 profile/persona**（人格描述）
- 可运行的"我的数字副本" → **L4 Project**（人格实例，非描述）

> 人格描述（源，进 Profile）与人格实例（编译产物，进 Project）分离，描述是 SSOT。

## 4. 版本与兼容

- 本 SPEC 为 v0.1，对应 goldenwave v0.1（标准 + 骨架，不含路由器）。
- L3 摄入路由器、L4 人格实例、蒸馏冷启动见 ROADMAP（v0.2 / v0.3+）。
- frontmatter 字段集向后兼容；新增字段必须先改 SPEC。
- 外部 producer 通过版本化 L3 Contract 接入，不依赖 GoldenWave 源码目录或 Git submodule。GoldenWave 拥有 Contract、validator 与兼容策略；producer 声明支持版本并通过契约测试。Malow 的具体关系见 [GoldenWave 与 Malow 集成合同](docs/malow-integration.md)。
