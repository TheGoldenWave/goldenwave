---
feature_id: goldenwave-strategy
document: approved-amendment
status: active
approved: 2026-07-27
supersedes_sections:
  - PRD.md#phase-0
  - PRD.md#phase-1
---

# 组织方式减重修订案

## 决定

保留 GoldenWave 的安全、隐私、来源、确认和恢复红线，但将执行方式从“完整体系先行”调整为“最小可信纵向闭环先行”。本修订案覆盖战略 PRD 的 Phase 0 Gate 组织方式与 Phase 1 交付顺序，不改变产品定位、北极星、Phase 2 指标或正式发布标准。

## Phase 0 Gate 调整

- **内部开工 Gate**：文档无定位冲突；人工代理 baseline 可复核；20 个任务覆盖 Profile、Knowledge、Project；Threat Model 通过评审。通过后可进入内部 Phase 1A dogfood。
- **外部验证 Gate**：两名外部设计伙伴知情同意并确认核心问题存在。它继续阻塞公共产品有效性结论、稳定 Contract 和正式发布，但不阻塞内部 Phase 1A。
- P0-08 作为并行外部验证泳道继续执行，不降低样本要求。

## Phase 1 切片

### Phase 1A — Safe Bootstrap

交付安全 `init`、只读 `doctor`、现有库只读 adopt inventory、存储等级与 Git 泄露诊断。Gate 要求初始化幂等、真实库诊断诚实、敏感信息误入 Git 为 0，且 doctor 不修改用户文件。

### Phase 1B — Candidate Contract

交付 experimental `context-candidate/v0.1`、fixtures、Validator、来源与新鲜度检查、内容/指令分离、稳定错误码，以及最小 `review / accept / reject`。Gate 要求非法和未确认候选 fail closed，正式写入只发生在显式 accept 后。

### Phase 1C — Reliable Inject

交付稳定 ID、幂等键、CAS、事务式多文件写入、崩溃与并发恢复、备份恢复证据，以及受控 adopt 修复。Gate 要求安全与恢复测试无 skip/pending，真实 KnowledgeBase 演练通过。

统一 `goldenwave` CLI 随三个切片形成，不单独建设命令空壳。具体排期在 Phase 0 内部开工 Gate 后依据 baseline 重新估算。

## 协作减重

- A 级安全、Contract、正式写入和恢复任务保留完整双重独立评审。
- B 级只读诊断和内部确定性模块采用测试先行加一次独立评审。
- C 级文档、状态和无行为变更采用作者自检加主 Agent 复核。
- 维护者 Harness 与用户产品分发分离；物理去重在引用盘点后执行。

## Baseline 兼容

`tests/specs/phase0/real-dogfood-tasks-v0.1.yaml` 已将 `PRD.md` 的 2026-07-25 内容摘要冻结为 baseline 输入。为保护在途运行的可重放性，本次不修改该 suite、不更新其摘要，也不把本修订案反向写入 v0.1 Oracle。Roadmap、执行看板、process 和本修订案表达当前组织状态；v0.1 baseline 继续衡量修订前已登记口径。
