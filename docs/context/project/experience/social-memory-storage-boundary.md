# Social Memory：Git 审计与可撤回数据的边界

## 决策

逻辑层不等于物理存储。L1/L2/L4 定义内容语义，`git_tracked/local_private/ephemeral` 定义副本、远端与删除能力。

需要保证撤回或硬删除的第三方数据不得进入 Git 历史。Social Memory 默认 local_private；原始聊天默认 ephemeral；只有用户明确允许长期保留的摘要才可 git_tracked。

## 原因

普通 Git 删除只改变当前树，历史提交、远端 clone、缓存和派生索引仍可能保留内容。若系统在数据进入 Git 后承诺“已硬删除”，会形成不可兑现的隐私保证。

## 通用规则

1. 在写入前决定 storage_class，不在落库后补救。
2. 日志、路径、索引和错误信息也必须服从存储策略。
3. 撤回要传播到正文、缓存、索引、派生视图和反向引用。
4. Git 中的数据只有完成历史重写、远端协调和副本验证后才能声称已 purge。

## 来源

- `docs/prd/social-memory/PRD.md`
- `docs/context/technical/social-memory/domain-model.md`
