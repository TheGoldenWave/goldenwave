---
name: goldenwave-profile
description: 维护 goldenwave 的 L1 事实层（9 事实域 + persona 人格域）。当用户要录入/更新个人事实、维护人格描述、核验过期数据时触发。
---

# goldenwave-profile

维护 L1 Profile（见 spec/L1-profile.md、spec/governance.md）。

## 操作
- **add-fact <内容>**：判断归属域 → 写入 → 更新 profile/INDEX。
- **update <域>**：按 maintainer 权限更新；冲突保留旧值+时间戳。
- **verify**：扫 `verified` 超 `refresh` 的文件，提醒/提议更新。
- **persona**：维护人格描述（expression-dna/traits/decision-style/voice-samples）。

## 规则
- frontmatter：id/domain/title/sensitivity/maintainer/refresh/verified/source/related。
- 绝不存凭据；只存实体关联指针。
- L3 数据引用须声明核验截止日。
- 人格描述进 persona（源）；人格实例属 L4，不在此。
