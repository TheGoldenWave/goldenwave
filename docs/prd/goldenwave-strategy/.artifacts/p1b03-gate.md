---
feature_id: goldenwave-strategy
task_id: P1B-03
stage: phase-1b-gate
status: ready-for-independent-review
updated: 2026-08-16
---

# P1B-03 Contract 安全验收与 Phase 1B Gate

## Scope

本 Gate 只验收 Candidate Contract v0.1、Validator 和 P1B-02 的 review/accept/reject 单候选写入；CAS、跨进程幂等、事务式多文件提交、崩溃协调和备份恢复仍属于 Phase 1C。

## Reproducible Evidence

在当前工作区执行：

```text
ruby tests/specs/candidate-decision/run.rb
ruby tests/specs/candidate-contract/run.rb
ruby tests/specs/goldenwave-init/run.rb
ruby tests/specs/phase0/goldenwave-strategy.spec.rb
python3 -m py_compile scripts/goldenwave_candidate.py scripts/gw_candidate/*.py
git diff --check
```

结果：

- Candidate Decision：`32 runs / 1472 assertions / 0 failures / 0 errors / 0 skips`；Python safe-write `22`、workflow `12` 均通过。
- Candidate Contract：`13 runs / 173 assertions / 0 failures / 0 errors / 0 skips`。
- GoldenWave Init：`20 runs / 178 assertions / 0 failures / 0 errors / 0 skips`。
- Phase 0：`3 runs / 9 assertions / 0 failures / 0 errors / 0 skips`。
- Python 编译与 `git diff --check`：通过。

## Security Matrix

| Boundary | Evidence | Result |
|---|---|---|
| 未确认、Candidate ID 或 reviewed digest 不匹配 | Candidate Decision binding tests | fail closed，无写入 |
| 来源不足、过期/未来 Candidate、恶意 envelope、重复键、未知字段和非法路径 | Candidate Contract fixtures | fail closed，诊断脱敏 |
| `local_private` / `ephemeral` accept、授权元组缺失、Git 历史未确认 | authorization/storage tests | fail closed，无正式写入 |
| target traversal、symlink parent、hardlink、错误 KB marker | safe-write/workflow adversarial tests | fail closed |
| 决策冲突、已有目标/回执、重复重试 | exclusive decision claim and conflict tests | 不覆盖、不产生矛盾回执 |
| fsync 边界故障与目标清理不确定 | safe-write/workflow fault matrix | 诚实区分 `failed` / `indeterminate` / `applied` |
| 回执与 CLI 诊断泄露正文、source_ref 或 clear target | redaction assertions | 无敏感正文、source_ref 默认隐藏 |

## Gate Decision

- 所有已执行 Gate suite 均无 failure、error、skip；测试中保留的平台能力条件分支本次未触发 skip。
- P1B-02 非作者最终评审已为 `Approved`，无剩余 Critical/Major；本 Gate 仍需独立 QA/architect 签署后才可将任务状态改为 `done`。
- Phase 1B 通过后，Phase 1C 只从新的事务注入接口开始，不回改 Contract v0.1 的冻结结构。

## Independent Review Record

- QA：待签署
- Architect/security：待签署
- Primary：待复核
