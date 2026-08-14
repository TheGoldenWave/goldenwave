# GoldenWave 与 LifeSub 生态关系

- 状态：产品关系已定义，运行时 Contract 待设计
- 日期：2026-08-14
- 关联项目：[LifeSub / 旁白](https://github.com/TheGoldenWave/LifeSub)

## 1. 关系结论

LifeSub 是本地优先的个人声音记忆系统，GoldenWave 是个人 AI 上下文治理层。两者互补，但拥有不同的数据真相：

| 项目 | 负责 | 不负责 |
|---|---|---|
| LifeSub | 音频采集、ASR、摘要、带时间戳证据、情境记忆、Agent 检索与访问审计 | 不直接把模型摘要写成 GoldenWave 正式知识 |
| GoldenWave | 对事实、知识、经验和工作流候选执行来源、确认、审计、撤回与版本治理 | 不保存或播放 LifeSub 原始录音，不复制完整声音记忆库 |
| Malow | 在 Project / Matter 中组织持续工作、对话、来源和用户确认 | 不成为音频采集或个人长期记忆的第二事实源 |

    LifeSub local memory
      owns: audio / transcript / episodic memory / evidence
                    |
                    | user-selected candidate with provenance
                    v
    GoldenWave governance
      owns: validate / review / accept / reject / inject / revoke
                    |
                    v
    Governed Profile / Knowledge / Project context

## 2. 源码与运行时边界

GoldenWave 与 LifeSub 是并列、独立发布的源码项目：

- 不使用 Git submodule。
- 不互相 vendoring 整个仓库。
- 不把用户记忆仓库放进任一公开源码仓库。
- LifeSub 通过版本化 Contract 或 Core API 适配 GoldenWave，不依赖 GoldenWave 内部目录细节。
- GoldenWave 可以验证 LifeSub 产生的候选，但不能把“验证通过”等同于“已写入正式知识”。

LifeSub 自身的 GitHub 记忆同步使用用户独立的私有仓库。公开的 LifeSub 与 GoldenWave 仓库只保存代码、规范和脱敏 fixture。

## 3. 候选晋升路径

推荐的数据流是：

1. LifeSub 在本地记录会议或重要对话。
2. LifeSub 生成带来源、时间范围、模型记录和敏感级别的记忆。
3. 用户选择值得长期沉淀的内容。
4. LifeSub 生成最小化候选，只包含治理所需内容与证据引用。
5. GoldenWave 对候选执行验证、review、accept/reject 和正式 inject。
6. GoldenWave 保存可审计的长期资产；LifeSub 继续保存原始声音证据。

首版不允许 LifeSub：

- 静默修改 GoldenWave 的 L1/L2/L4 正式内容。
- 将整段录音或完整转写默认复制进 GoldenWave。
- 绕过用户确认，把 ASR 或摘要直接视为事实。
- 因候选被撤回而删除 LifeSub 原始记录，或反向自动恢复已删除的原始记录。

## 4. 最小 Contract 方向

正式字段尚待双方设计。候选至少需要表达：

- Contract 版本与稳定候选 ID。
- LifeSub 记忆 ID、来源类型和时间范围。
- 候选内容及其类型：事实、知识、决定、经验或 Project context。
- 证据引用和生成方式，而不是默认附带完整原文。
- 用户确认状态和确认时间。
- 敏感级别、允许的目标层和保留策略。
- ASR 与摘要 Provider 的可审计元数据。

GoldenWave 对未知主版本、缺失来源、越权目标或未经确认的候选必须 fail closed。

## 5. Agent 检索边界

LifeSub 通过自己的 Core 和插件向 Codex、DeepSeek Harness、Malow 等 Agent 提供情境记忆检索。GoldenWave Serve 负责治理后的长期上下文。Agent 可以在一次任务中同时使用两类来源，但必须保留来源边界：

- LifeSub 结果标识为带时间证据的情境记忆。
- GoldenWave 结果标识为经过治理的长期上下文。
- Agent 不得把模型推断伪装成 LifeSub 原文或 GoldenWave 已确认事实。

## 6. 迭代顺序

1. LifeSub 先完成本地“记录 -> 记忆 -> Agent 检索”闭环。
2. 双方共同定义候选 Contract 与脱敏 fixture。
3. GoldenWave 提供 validator 和兼容策略。
4. LifeSub 实现窄 Adapter 与契约测试。
5. 真实用户验证后，再评估自动候选建议；正式写入继续由 GoldenWave 治理。

