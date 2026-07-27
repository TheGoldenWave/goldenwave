---
feature_id: goldenwave-strategy
task_id: P0-09
gate: phase-0-internal-start
status: pass
updated: 2026-07-27
decision: go-for-phase-1a
---

# P0-09 内部开工 Gate Review

## Gate 口径

本评审采用 [amendments/2026-07-27-organization-lightening.md](../amendments/2026-07-27-organization-lightening.md) 中已批准的内部开工 Gate，而非战略 PRD 旧版 Phase 0 外部验证口径。内部 Gate 通过后可以进入 Phase 1A dogfood；外部设计伙伴验证仍单独阻塞公共产品结论、稳定 Contract 和正式发布。

内部 Gate 四项准入条件：

1. 文档无定位冲突。
2. 人工代理 baseline 可复核。
3. `20` 个任务覆盖 Profile / Knowledge / Project。
4. Threat Model 通过评审。

## 证据输入

| Gate 条件 | 证据 | 结论 |
|---|---|---|
| 文档无定位冲突 | E-P0-02, E-P0-07 | pass |
| baseline 可复核 | E-P0-05b, E-P0-06 | pass |
| `20` 个任务覆盖三类上下文 | E-P0-05a, E-P0-05b | pass |
| Threat Model 通过评审 | E-P0-04 | pass |

补充说明：

- P0-07 已完成外部验证所需的协议与访谈材料包，但未伪造任何邀请、知情同意或访谈结果。
- P0-08 仍缺真实外部联系动作，保持外部泳道状态，不计入内部 Gate 完成条件。

## 2026-07-27 复跑检查

已执行以下命令并得到通过结果：

```bash
ruby tests/specs/phase0/p0-baseline-preflight.rb \
  --runs tests/evidence/phase0/run-manifests/p0-v0.1-run-ids.yaml

ruby tests/specs/phase0/goldenwave-strategy.spec.rb

ruby tests/specs/phase0/p0-scorecard-metadata-validate.rb \
  --runs tests/evidence/phase0/run-manifests/p0-v0.1-run-ids.yaml \
  --scorecard tests/evidence/phase0/run-manifests/p0-v0.1-scorecard-metadata.yaml
```

结果摘要：

- preflight 返回 `status=ok`，`suite_status=preregistered`，`evidence_status=confirmed`，`run_ids=20`；
- Phase 0 Ruby spec `3 runs / 9 assertions / 0 failures / 0 errors / 0 skips`；
- scorecard validator 返回 `status=ok`，`scorecard_entries=20`，`run_ids=20`。

## Gate 结论

内部开工 Gate 结论为 `GO`。

允许进入的下一阶段：

- Phase 1A `Safe Bootstrap`
- 仅限内部 dogfood、只读诊断与安全初始化闭环

仍然保留的约束：

- P0-08 未完成，不得对外声称通用性已验证；
- 稳定公共 Contract、公共产品有效性结论和正式发布仍需两名外部设计伙伴证据；
- Phase 1A 期间继续保持 `remote_model` 默认拒绝、正式写入需显式 accept 的既有约束。

## 后续动作

1. 将执行看板与 process 同步到 `phase-1a-ready`。
2. 启动 P1A-01 的 RED 测试与失败验收。
3. 保持 P0-08 为 `todo`，直到用户完成真实引荐或邀请发送。
