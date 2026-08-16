---
feature_id: goldenwave-strategy
updated: 2026-07-27
---

# GoldenWave Strategy Notes

## 2026-07-24 — 外层入口引用不可解析

- 现象：会话外层注入的指令包含 `@RTK.md`，但实际仓库 `AGENTS.md` 不含该引用，仓库和 Git 历史也从未存在 `RTK.md`。
- 结论：这是外层兼容上下文，不是项目入口缺失。当前及首次引入提交中的 `AGENTS.md` 均为完整入口。
- 处理：不创建虚假 `RTK.md`，不修改有效的仓库入口；后续以工作区 `AGENTS.md` 为项目权威规则。

## 2026-07-24 — 决策包重复请求

- 现象：初版决策包把已由战略批准的 local-first、experimental Contract、Social Memory 延后等事项再次提交用户。
- 原因：把架构约束确认误当成新产品决策。
- 规则：后续生成决策包前，先检索 PRD/ADR 的已批准决策；只有剩余 D2 分歧才请求用户。

## 2026-07-27 — 动态来源不能直接充当冻结 fixture

- 现象：真实任务 suite 最初按路径冻结 `ROADMAP.md`、`process.md` 和执行看板；完成用户确认后按规范更新进度，会立即造成来源摘要不匹配。
- 原因：把持续变化的项目状态文件同时当成不可变测试输入，形成确认后自失效循环。
- 规则：可重放测试必须引用不可变脱敏 snapshot，并在 snapshot frontmatter 保存原路径、观察时间和原内容摘要；live 文件只用于后续状态管理。

## 2026-07-27 — 未确认的 owner-bound baseline 必须隔离

- 现象：工作区曾出现一组在 suite 仍为 pending 时生成的 baseline 报告；其中 owner-bound 任务被记为通过，原始运行引用也无法复核。
- 处理：将产物移入 `tests/evidence/phase0/quarantine/preconfirmation-2026-07-25/` 并标记 `.invalid`，禁止进入 Gate、指标或重放。
- 规则：生成 scorecard 前必须先运行 P0-06 preflight；它要验证 suite 已确认、绑定与摘要一致、运行清单位于允许目录且 run ID 非空唯一。

## 2026-07-27 — 项目组织方式减重

- **用户决定**：保留 GoldenWave 的安全与治理红线，但从“完整体系先行”调整为“最小可信纵向闭环先行”。
- **阶段调整**：Phase 1 拆为 1A Safe Bootstrap、1B Candidate Contract、1C Reliable Inject；每个切片独立验收后再扩大能力。
- **Gate 调整**：Phase 0 内部基线与 Threat Model 通过即可启动内部 Phase 1A；外部设计伙伴继续阻塞公共产品结论和正式发布，不阻塞内部 dogfood。
- **协作调整**：开发闭环按 A/B/C 风险分级，低风险文档与状态更新不再强制双重独立评审。
- **仓库边界**：维护者 Harness 与用户产品分发分离；物理去重必须在引用盘点后执行，不在本次调整中直接删除。

## 2026-07-27 — 仓库 scorecard metadata 必须 fail-closed

- 现象：`p0-baseline-preflight.rb` 已验证 suite 绑定、确认摘要和 `run_id` 唯一性，但还不能阻止 repo scorecard 混入额外字段、私有路径或二次回答痕迹。
- 风险：一旦把 `.private/` 路径、自由文本评语或多轮补救记录写进仓库，P0-06 就会破坏 allowlist 边界，且难以自动复核。
- 处理：新增 `tests/specs/phase0/p0-scorecard-metadata-validate.rb` 与 `tests/specs/phase0/goldenwave-strategy.spec.rb`，把 repo scorecard 收紧为 9 个 allowlist 字段、固定嵌套键、opaque `evidence_refs`、单响应计数和 preregistered `run_id` 集合。
- 规则：P0-06 的仓库 scorecard 只能存 `tests/specs/phase0/real-dogfood-README.md` 明示 allowlist 字段；原始输出和带文本的 reviewer notes 仅允许进入 `.private/goldenwave/baselines/p0-v0.1/`。

## 2026-07-27 — P0-06 基线暴露来源归因缺口

- **结果**：20 个单响应 run 共通过 96/120 条断言，无 invalid；20 个任务均因至少一条断言失败而未全量通过。
- **主要缺口**：provenance 归因 0/20，通过内容本身无法稳定判断用了哪些冻结来源；另有 3 条 fact-value 和 1 条 workflow-fit 失败。
- **保留原则**：不提供第二次回答，不把 baseline 修绿；该结果作为 Phase 1A Context/Doctor 输出必须显式携带来源的 RED 输入。
- **计时限制**：5 个 run 使用批次级 65 秒边界，不能用于精确的单任务延迟比较；本批次只报告聚合观察。

## 2026-07-27 — P1B-01 覆盖率工具不可用

- 现象：Candidate Contract 验收和 Phase 1A 回归均通过，但当前 `python3` 环境没有 `coverage` 模块，系统也没有 `coverage` 命令。
- 处理：不伪造覆盖率数字；E-P1B-01 保持 `review`，分支覆盖率证据与 A 级独立 Contract/安全评审完成前不得标记 done。
- 规则：测试全绿不等于 Gate 完成；覆盖率工具缺失必须作为显式证据缺口保留。

## 2026-07-29 — P1B-01 覆盖率补齐

- 现象：项目指定的 Python 3.11 由 `uv` 管理并启用 PEP 668，拒绝直接安装 Coverage.py。
- 处理：在仓库忽略的 `.private/venvs/phase1b-coverage/` 建立隔离环境，安装与 Phase 1A 一致的 Coverage.py 7.15.2；测试通过 `GW_CANDIDATE_PYTHON` 注入覆盖率包装器，不修改产品运行时。
- 结果：补充合同版本、状态、ID、枚举、时间、嵌套类型、未知字段和运行时输入 fixtures 后，验收为 `5 runs / 125 assertions / 0 failures / 0 errors / 0 skips`，分支覆盖率 `97%`。
- 剩余 Gate：P1B-01 仍需 A 级非作者 Contract/安全评审，覆盖率不再是阻塞项。

## 2026-08-10 — 第三方复杂度审视与减重决定

- 盘点：已跟踪文件中 `.agents/`、`.claude/`、`.codex/` 占主要部分；`.agents` 与 `.claude` 存在大量完全相同的镜像副本。维护者 Harness 的复杂度已经明显高于当前产品实现。
- 判断：隐私、来源、Candidate 确认、安全写入与恢复属于必要复杂度；多套 Harness 镜像、重复状态来源和超前的流程治理属于优先消除的偶然复杂度。
- 用户决定：接受按“物理去重 -> 真实纵向闭环 -> 状态收敛 -> 对外认知简化 -> Contract 单一结构定义 -> 复杂度预算”的顺序推进。
- 格式原则：JSON Schema 当前继续作为结构 SSOT。字符数问题要区分低频 Schema 与高频实例；若提示词成本过高，从 Schema 生成紧凑投影，不手工维护第二套定义。
- 开放验证：可比较 JTD、CUE、TypeSpec、Protocol Buffers、MessagePack/CBOR 等方案，但替换必须用真实 Candidate 样本证明净收益，并计入新编译器、生成链和学习成本。

## 2026-08-16 — P1B-01 独立 Contract / 安全评审

- 初审结论：`Changes requested`。发现 Schema 不是运行时 SSOT、目标路径接受控制字符、时间解析宽于 RFC 3339、未知字段名和非法 Candidate ID 可进入诊断、深层 JSON 可触发未捕获递归异常。
- 处理：每项先写失败验收，再做最小修复；Schema 现负责字段、required、枚举、pattern 与 const，运行时只保留跨字段、安全和运行时语义。
- 复核：同一非作者 code reviewer 进行了三轮复核，最终 `Approved`，无剩余 Critical/Major/Minor。
- 集成结果：Candidate `13 runs / 173 assertions`、Phase 1A `19 / 165`、Phase 0 `3 / 9`，全部无 failure/error/skip；分支覆盖率 `95%`（`200` statements、`64` branches）。
- 工具经验：覆盖率包装器只用于被测 CLI 入口；测试内部的 `python -c` Schema 探针使用独立 `GW_RUNTIME_PYTHON`，避免 coverage 参数污染辅助命令。

## 2026-08-16 — P1B-02 Candidate Decision 闭环

- 设计结论：review 只读；accept/reject 必须绑定 Candidate ID 与 exact-byte SHA-256；accept 仅开放 `git_tracked`，并要求完整 store 授权元组、无 consent-required 数据声明和 Git 历史确认。
- 安全实现：所有声明写入通过 descriptor-relative `O_NOFOLLOW`、exclusive create、fstat regular/link-count、短写循环及文件/目录 fsync；写入结果区分 failed、indeterminate 和 applied。
- 决策一致性：accept/reject 先竞争共享 `<candidate_id>.decision.json`，防止顺序或并发产生矛盾回执；完整并发协调、CAS 和恢复仍属于 Phase 1C。
- 评审发现：系统时钟不能由调用者回拨；验证与写入必须拒绝非 NFC 和 bidi 控制路径；CLI 参数、Unicode 输出、lone surrogate 与 help 都必须保持结构化、脱敏、无隐藏 bytecode 写入。
- POSIX 边界：固定 dirfd 能防止路径替换重定向到另一个目录对象；最终验证后的非协作同 UID rename 无可移植无锁解法，明确纳入 Phase 1C/OS 信任模型，不在 P1B-02 过度承诺。
- 最终证据：Candidate Decision `32/1472`、safe-write `22`、workflow `12`、Contract `13/173`、Init `20/178`、Phase 0 `3/9` 全绿；综合分支覆盖率 `84%`；非作者最终 verdict `Approved`。

## 2026-08-16 — P1B-03 独立评审基础设施中断

- 现象：两次 QA 代理和一次 architect 代理均在启动后由平台返回 `stream disconnected before completion`，没有产生审查结论或文件改动。
- 处理：primary 已复跑完整 Gate 命令并保存 `p1b03-gate.md`，但不把自检替代独立签署；P1B-03 在新的 reviewer 成功复核前保持 `ready-for-independent-review`。
- 规则：代理基础设施错误不能降低 A 级 Gate，也不能被记录为 reviewer pass；允许继续准备下一阶段的设计和 RED fixture，但不得把 Phase 1B 状态标记为 done。

## 2026-08-16 — P1C Reliable Inject 加速复审

- P1C-01 RED/GREEN：稳定 operation ID、幂等 replay、active-base CAS、同 base 并发、提交后 indeterminate、恢复、backup/restore 与 CLI 黄金路径；focused `8 tests` 全绿。
- P1C-01 复审：第一轮发现提交点后 materialization 异常结果不诚实、缺并发证据；第二轮发现 backup symlink、atomic 短写和管理记录 symlink 风险；均以针对性测试修复，Critical=0，Important=0，Minor 不阻塞。
- P1C-02 复审：repair 初版发现 symlink parent 和无 marker 目录可被修改，定级 Critical 并修复；repair `2/9`、Init `22/187` 全绿。
- 真实库边界：`readonly_gate.rb /Users/goldenwave/KnowledgeBase` 返回 `unchanged=true`，但 doctor/adopt 仍报告现有 manifest/ignore/结构阻断；未获新授权前不执行真实写入或 repair。
