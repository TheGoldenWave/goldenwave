# goldenwave SPEC v0.2-draft

> 本文件是 GoldenWave 的“宪法”：定义个人 AI 上下文治理层的信息模型、目录布局与不可破原则。
> 所有 Skill、脚本、模板都必须遵守本 SPEC。变更 SPEC 优先于变更实现。

GoldenWave 当前处于 experimental 阶段，不承诺稳定 API 或公共兼容性。“个人 AI 操作系统”是长期愿景，不是本版本产品边界。

## 0. 设计哲学

1. **本地优先**：数据存在用户机器上，云是可选增强，不是依赖。
2. **文本优先，按风险审计**：L1/L2/L4 的长期资产优先使用 Markdown 等可读文本。允许长期保留的内容可进入 Git；需要保证撤回或硬删除的第三方数据必须使用 `local_private`，原始临时材料使用 `ephemeral`，不得进入 Git 历史。L3 envelope、Schema 和 validator 可以使用 JSON/JSONL 等文本格式，但不能绕过治理门禁成为正式内容。
3. **人机共读**：frontmatter 是机器协议（agent 先读它判断），正文是人机共享语义层。
4. **三维分层**：知识（可复用）/ 事实（此刻为真）/ 人格（怎么想怎么说）严格分离，互不污染。
5. **标准写进库，不绑工具**：规则存在知识库里（如 CLAUDE.md / AGENTS.md），任何遵守 SPEC 的 agent 都能接管。
6. **严格生产，宽松读取**：新建/实质修改必须合规；存量可渐进修复。

## 1. 五层架构

五层是上下文的信息与治理模型，不代表 GoldenWave 要自建五类应用。当前产品运行模型是：Store 表达长期上下文，Govern 管理 Candidate，Serve 生成任务级 Context Pack，Learn 从运行中产生受治理候选。Agent Runtime、任务编排、编辑器和数据捕获器属于外部系统。

| 层 | 职责 | 载体 | 回答的问题 |
|---|---|---|---|
| L1 Profile | 管用户中心事实（含人格描述与社交关系） | `profile/` + `.private/` | 关于我及与我有关的当前事实 |
| L2 Knowledge | 管沉淀 | `wiki/` | 世界如何运作 / 我如何思考 |
| L3 Knowledge Governance Workflow | 管知识治理流转 | 脚本 + 协议 | 候选如何 capture、route、score、confirm、inject 和 sync |
| L4 Project | 管目标执行 | 项目目录 + Skill | 为某目标做事并形成可复用能力（含人格实例） |
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
│   ├── 01-body-health/ 02-finance/ 03-consumption/
│   ├── 04-social/           # 可跟踪的 Social Memory 摘要与安全索引
│   ├── 05-time-energy/ ... 09-career-assets/
│   └── persona/            # 人格描述
├── .private/                # local_private；不进入任何 Git 历史
│   └── social/              # 人、组织、关系、互动与承诺的高敏正文
├── projects/               # L4 执行层（可选）
├── inbox/                  # 待处理原料（L3 入口）
├── .sources/               # 来源归档（不进主图谱）
└── .kb/                    # 脚本 / 日志 / 模板
    ├── log.md  scripts/
```

## 3. 三维分层的判定口诀

- 会随时间频繁变、查来取值 → **L1 Profile**（事实）
- 描述“我与谁/哪个组织如何相连、发生过什么、需要履行什么” → **L1 profile/04-social**（Social Memory）
- 读来理解、换工作仍有效 → **L2 Knowledge**（知识）
- 描述"我怎么想/怎么说话" → **L1 profile/persona**（人格描述）
- 可运行的"我的数字副本" → **L4 Project**（人格实例，非描述）

> 人格描述（源，进 Profile）与人格实例（编译产物，进 Project）分离，描述是 SSOT。

## 4. 逻辑层与存储等级

- L1/L2/L4 决定内容的**语义归属**；`git_tracked/local_private/ephemeral` 决定内容的**物理存储与副本策略**，两者不得混为一谈。
- `git_tracked`：用户明确允许长期保留的内容，可进入 Git；普通删除不等于清除历史。
- `local_private`：需要本地保存且支持撤回/硬删除的内容，不进入任何 Git 历史或未授权远程模型。
- `ephemeral`：原始聊天、临时导入等处理材料，处理后清理，不进入正式层。
- 任何要求保证硬删除的数据不得选择 `git_tracked`。详细规则见 `spec/governance.md`。
- Knowledge Base 根 `.gitignore` 必须排除 `.private/`；`git_tracked` 是唯一允许 `git add` 的存储等级。
- `goldenwave validate/doctor` 必须在 `.private/` 缺少 ignore 规则或任一 local_private 文件已被 Git 跟踪时 fail closed。在该门禁实现前，Social Memory 规范不可宣称由工具自动保障。

## 5. 版本与兼容

- v0.1 对应标准 + 骨架；本文件现为 v0.2-draft，加入 Candidate 治理与分级存储规范，运行时尚未完整实现。
- 当前优先实现 Trustable Core、Context Pack 与跨 Agent 验证。Social Memory Contract、人格实例和蒸馏冷启动均为 Gate 之后的候选方向，见 ROADMAP。
- frontmatter 字段集向后兼容；新增字段必须先改 SPEC。
- 外部 producer 通过版本化 L3 Contract 接入，不依赖 GoldenWave 源码目录或 Git submodule。GoldenWave 拥有 Contract、validator 与兼容策略；producer 声明支持版本并通过契约测试。Malow 的具体关系见 [GoldenWave 与 Malow 集成合同](docs/malow-integration.md)。
