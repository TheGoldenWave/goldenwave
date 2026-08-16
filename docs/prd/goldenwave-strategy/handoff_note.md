---
feature_id: goldenwave-strategy
stage: phase-1b-p1b03-ready
status: ready
updated: 2026-08-16
branch: codex/sync-agentic-project
remote_head: 75db9ef9e5160c8f22147ce02e0a773e162ceaa1
---

# GoldenWave Phase 1B 工程移交说明

## 新会话先读

1. 根 `AGENTS.md` 与 `.claude/contexts/review.md`。
2. `.artifacts/process.md`、`.artifacts/execution-board.md`、`.artifacts/evidence-manifest.md`。
3. `docs/context/technical/goldenwave/candidate-decision-design.md`。
4. `contracts/context-candidate/v0.1/README.md` 与 `docs/context/technical/goldenwave/threat-model-v0.1.md`。

当前状态是 **P1B-02 done，P1B-03 ready**。下一任务是 Contract 安全验收与 Phase 1B Gate，不是继续扩展功能，也不是升级 Contract 版本。

## Git 与工作区状态

- 当前分支：`codex/sync-agentic-project`。
- 远端同名分支当前停在 `75db9ef`；P1B-01 后续安全修复和完整 P1B-02 尚未提交或推送。
- 工作区是有意保留的 dirty state，不得 reset、checkout 或覆盖。
- `.DS_Store` 与 `docs/prd/turing-outbound-config/` 不属于 GoldenWave Phase 1B，提交时必须排除。
- 在提交前重新执行 `git status --short`，只暂存 GoldenWave P1B-01/P1B-02 相关文件。

## 已完成能力

### P1B-01 Candidate Contract

- `context-candidate/v0.1` JSON Schema 是字段、required、enum、pattern 与 const 的结构 SSOT。
- Validator 负责跨字段时间、来源、目标路径、内容即数据和安全语义。
- 拒绝重复键、未知字段、非 RFC 3339、过期/未来 Candidate、控制字符、非 NFC 和 bidi target、lone surrogate。

### P1B-02 Candidate Decision

- `review`：只读、本地显式内容披露、exact-byte SHA-256、默认隐藏 `source_ref`。
- `accept`：只支持 `git_tracked`；要求 Candidate ID + reviewed digest + 完整 `store` 授权元组 + 无 consent-required 数据声明 + Git 历史确认。
- `reject`：不写正式层，只接受受控 reason code。
- accept/reject 先竞争共享 `<candidate_id>.decision.json`，顺序和并发矛盾决策只能有一个赢家。
- 正式写入和回执使用 descriptor-relative `O_NOFOLLOW`、exclusive create、regular/nlink 校验、短写循环、文件与目录 fsync。
- 结果诚实区分 `failed / indeterminate / applied / rejected`，不把不确定清理报告为成功失败。
- 决策命令使用系统 UTC；调用者不能通过 `--now` 回拨时间。只有 `validate` 保留显式 `--now`。

## 当前 CLI

```bash
python3 scripts/goldenwave_candidate.py validate candidate.json --now 2026-08-16T12:00:00+08:00
python3 scripts/goldenwave_candidate.py review candidate.json
python3 scripts/goldenwave_candidate.py accept candidate.json \
  --target /path/to/KnowledgeBase \
  --confirm cand_... \
  --review-digest <sha256> \
  --authorization-basis self_context \
  --retention-until none \
  --attest-no-consent-required-data \
  --ack-git-history
python3 scripts/goldenwave_candidate.py reject candidate.json \
  --target /path/to/KnowledgeBase \
  --confirm cand_... \
  --review-digest <sha256> \
  --reason privacy
```

不要用真实个人 Knowledge Base 测试 accept，除非用户再次明确授权。P1B-03 默认使用临时 sandbox KB。

## 最新验证证据

- Candidate Decision CLI：`32 runs / 1472 assertions`。
- Safe Write：`22 tests`。
- Workflow：`12 tests`。
- Candidate Contract：`13 runs / 173 assertions`。
- GoldenWave Init：`20 runs / 178 assertions`。
- Phase 0：`3 runs / 9 assertions`。
- 全部 `0 failures / 0 errors / 0 skips`。
- 合并覆盖率：`766 statements / 230 branches / 84%`。
- 非作者最终评审：`Approved`，无剩余 Critical/Major。

标准复跑命令：

```bash
ruby tests/specs/candidate-decision/run.rb
ruby tests/specs/candidate-contract/run.rb
ruby tests/specs/goldenwave-init/run.rb
ruby tests/specs/phase0/goldenwave-strategy.spec.rb
python3 -m py_compile scripts/goldenwave_candidate.py scripts/gw_candidate/*.py
git diff --check
```

## 下一任务：P1B-03

P1B-03 是验收/Gate 任务，建议按以下顺序执行：

1. QA 冻结 Phase 1B Gate checklist，不新增产品能力。
2. 在临时 KB 运行合法 review/accept/reject 黄金路径，核对 target 和全部脱敏回执。
3. 复跑未确认、digest 变化、来源不足、恶意内容、过期 Candidate、授权不足、非 git storage、路径攻击、冲突决策和 indeterminate 故障矩阵。
4. 确认所有正式写入都有共享 decision claim、authorization/applied receipt 和 Candidate digest，可追溯但不泄露正文/source_ref/clear target。
5. 独立 QA + architect/code-reviewer 签署 E-P1B-03；无 Critical/Major、无 skip 后才标记 Phase 1B Gate pass。
6. Gate 通过后，下一阶段才是 P1C-01：稳定 ID、幂等、CAS 与事务式 inject。

## 不得提前实现

- 不在 P1B-03 实现 CAS、锁、重试幂等、claim 恢复、事务式多文件提交或崩溃协调。
- 不开放 `local_private` / `ephemeral` accept；v0.1 尚无安全私有目标映射。
- 不宣称抵御最终 inode 验证后的非协作同 UID namespace rename；该风险属于 Phase 1C/OS 信任模型。
- 不执行 Git commit/push、真实 KB 写入、远程模型调用或网络操作，除非用户明确要求。
- 不修改冻结的 Phase 0 baseline snapshots/Oracle 来让状态变绿。

## 关键文件

- `scripts/gw_candidate/schema.py`：Schema SSOT 加载。
- `scripts/gw_candidate/validator.py`：Candidate 安全校验。
- `scripts/gw_candidate/decision.py`：digest、授权和回执构造。
- `scripts/gw_candidate/safe_write.py`：descriptor-relative 单文件持久化。
- `scripts/gw_candidate/workflow.py`：decision claim 与 accept/reject 状态机。
- `scripts/gw_candidate/cli.py`：结构化 CLI 边界。
- `tests/specs/candidate-decision/`：P1B-02 黑盒与对抗测试。
- `tests/evidence/phase1b/coverage-summary.txt`：最新覆盖率证据。

## 推荐的新会话启动语

```text
请读取 docs/prd/goldenwave-strategy/handoff_note.md，并按其中状态恢复 GoldenWave。
当前 P1B-02 已完成，直接推进 P1B-03 Contract 安全验收与 Phase 1B Gate。
先检查 dirty worktree，不要覆盖未提交的 P1B-01/P1B-02，也不要纳入 .DS_Store 或 docs/prd/turing-outbound-config/。
默认使用临时 sandbox KB，不写真实个人 Knowledge Base；按 A 级闭环执行 QA Gate、独立安全评审、全量回归和证据更新，直至 P1B-03 完成。
```
