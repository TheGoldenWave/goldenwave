---
feature_id: social-memory
stage: handoff
status: ready
updated: 2026-07-23
---

# Social Memory 工程移交说明

## 已冻结的产品边界

- 以 `self` 为唯一锚点，帮助用户维护真实关系。
- V1 支持 Person、Collective、Relationship、Affiliation、Interaction、Commitment。
- Social Memory 默认 `sensitivity: L3`、`storage_class: local_private`、`maintainer: human`。
- 原始聊天默认 ephemeral；Agent 不自动发送、分享、合并或写入敏感推断。

## 下一交付物

1. `social-memory-patch/v0.1.0` JSON Schema。
2. 合法/非法 fixture：身份、时态、授权、合并、撤回、Git 泄露场景。
3. validator 与 `merge-check / consent-check / redact` 策略接口。
4. local_private 与 ephemeral 存储适配器及 purge 行为。
5. profile/ingest Skills 与 `social add/log/brief/review/forget` CLI 行为。

## 工程门禁

- 先写 `tests/specs/` 验收测试，再实现 Schema、validator 或存储适配器。
- 任何失败都必须 fail closed，不得通过降级跳过授权。
- 不允许姓名进入默认文件名、日志或错误遥测。
- 不允许宣称 Git 中的数据已硬删除，除非历史与远端副本均完成 purge 验证。

## 参考

- [PRD](PRD.md)
- [领域模型](../../context/technical/social-memory/domain-model.md)
- [正式 SPEC](../../../SPEC.md)
- [治理规范](../../../spec/governance.md)
