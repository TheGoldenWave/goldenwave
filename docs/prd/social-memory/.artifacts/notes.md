# Social Memory 决策与风险记录

## 2026-07-23 — 以 self 为唯一锚点

- **决定**：V1 只建模 `self <-> Party` 的 Relationship，不构建任意第三方之间的完整社交图谱。
- **原因**：产品目标是帮助用户维护真实关系，不是监控或画像他人。

## 2026-07-23 — Person 与 Collective 同为一等对象

- **决定**：家庭、朋友圈、团队、公司、社群和 household 统一为 Collective 子类型。
- **边界**：Collective 只保存与用户关系相关的上下文，通用组织知识仍归 L2/L4。

## 2026-07-23 — 隐私优先于 Git 完整性

- **问题**：进入 Git 历史的第三方数据无法可靠承诺硬删除。
- **决定**：引入 `git_tracked / local_private / ephemeral` 存储等级。需要保证撤回的数据不得进入 Git。
- **影响**：`SPEC.md` 中“正式知识皆 Markdown + Git”需要增加受保护数据例外。

## 2026-07-23 — 用户批准分级存储

- **确认**：用户接受 `git_tracked / local_private / ephemeral` 三类存储等级。
- **结果**：该方案已写入 `SPEC.md`、L1、L3、governance、README、ROADMAP 与路由器 PRD。

## 2026-07-23 — 高信任、低自动化

- **决定**：Agent 可以整理、提醒和草拟，但不得自动发送、分享、合并身份或将敏感推断写入正式层。
- **质量门禁**：未授权分享、敏感推断直写和静默错误合并的验收目标均为 0。
