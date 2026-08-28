# Governance 规范（治理）

> 跨层治理：敏感度、用途授权、存储等级、新鲜度、证据与撤回。v0.2-draft 先定义规范，validator 与运行时门禁按 ROADMAP 落地。

## 1. 敏感度四级
| 级别 | 含义 | 示例 | 默认策略 | 可收紧为 |
|---|---|---|---|---|
| L0 | 公开 | 公开社媒/个人网站 | 可读；写入仍需来源 | 全放行 |
| L1 | 低敏 | 尺码/设备型号/日程偏好 | 本地可用；外发服从 agent-contract | 仅本地 |
| L2 | 中敏 | 常驻地/履历细节/通勤 | 本地处理；远程模型需授权 | 仅本地模型 |
| L3 | 极敏 | 病史/资产/亲友档案 | `local_private` + 分用途授权 | human-only |

`sensitivity` 只回答内容风险，不决定全部行为；任何处理还必须同时检查 policy tags、authorization scope 与 storage_class。访问矩阵统一配置在 `profile/console/agent-contract.md`。

## 2. Policy Tags

第三方或特殊类别数据使用正交标签表达处理限制，至少支持：

- `third_party`
- `minor`
- `health`
- `finance`
- `political`
- `romantic`
- `workplace`
- `credential_pointer`

标签只能收紧策略，不能把 L3 降为低敏。`minor/health/finance/political/romantic` 默认禁止远程模型、分享和自动建议，除非规范与授权均明确允许。

## 3. 存储等级

| 等级 | 允许内容 | Git/远端策略 | 删除能力 |
|---|---|---|---|
| `git_tracked` | 用户确认可长期保留的内容 | 可进入 Git；推远端仍受访问矩阵约束 | 普通删除不清除历史；硬删除需 purge |
| `local_private` | 默认 L3 与第三方社交数据 | 不进入任何 Git 历史，不交给未授权远程模型 | 支持受管范围内的本地硬删除与撤回传播 |
| `ephemeral` | 原始聊天、临时导入与处理中间材料 | 永不进入 Git，处理后清理 | 处理完成即删除 |

规则：

1. 语义层与存储等级正交；例如 Social Memory 正文逻辑上属于 L1，物理上可位于 `.private/social/`。
2. 要求保证撤回或硬删除的数据不得选择 `git_tracked`。
3. 从 local_private 升为 git_tracked 必须由用户确认，并明确普通删除无法清除 Git 历史。
4. 日志、文件名和索引不得通过旁路泄露 private/ephemeral 内容。
5. Knowledge Base 根 `.gitignore` 必须排除 `.private/`；init 必须生成该规则，不能只依赖用户记忆。
6. validate/doctor 发现 `.private/` 缺少 ignore、local_private 已被 Git 跟踪或 ephemeral 进入正式目录时必须 fail closed。

## 4. 新鲜度治理
- `verified`（最后核验日）+ `refresh`（周期）。
- facet 半衰期（借 OpenHuman）：身份 90d / 否决 60d / 风格 14d / 渠道 7d / 资产订阅 30d。
- 周期核验循环（v0.2）：扫超期文件，L1/L2 提醒、L3+agent 提议更新。

## 5. 证据分级（借 immortal）
- verbatim（原话）> artifact（成稿）> impression（旁人印象）。
- inference（模型推断）不是事实等级，只能作为待确认候选；确认后仍保留 inference 标记。
- 矛盾不静默覆盖：旧值移历史 + 新值带时间戳 + 标来源。

## 6. 用途授权

授权不能用一个布尔值概括，至少按以下 scope 分开记录：

- `store`：保存结构化记录；
- `summarize`：从原始材料生成摘要；
- `suggest`：用于提醒或行动建议；
- `share`：对外展示、导出或发送；
- `remote_model`：交给远程模型处理。

授权还必须记录 `basis`、`retention_until` 与 `revoked_at`。`basis` 至少包括：

- `self_context`：用户为维护自身关系保存最少必要的普通事实；
- `public_source`：有可核验的公开来源；
- `explicit_consent`：数据主体对对应处理用途明确同意，不等于用户单方点击确认。

蒸馏自己默认允许；第三方敏感属性、人格推断、share 与 remote_model 默认要求 explicit_consent。Agent 永远不能以“提高便利性”为由扩大授权范围。

## 7. 撤回与删除传播

撤回必须阻断后续使用，而不只是修改当前页面：

1. 标记对象 `revoked`，停止查询、建议、简报、导出和自动重建；
2. 清理 local_private 正文、缓存、搜索索引与派生摘要；
3. 删除或脱敏 Interaction/Commitment 中的反向引用；
4. 仅保留不含身份信息的最小 tombstone，防止误重建；
5. 若数据曾进入 Git，必须明确提示普通删除不等于硬删除，并提供历史 purge 与远端协调路径。

GoldenWave 的 purge 保证只覆盖其管理的正文、索引、缓存和派生视图。用户自建备份、文件系统快照、外部导出或已发送副本必须在 purge report 中列为未解决副本；未验证这些副本前不得宣称“已从所有位置删除”。

## 8. 设计红线
1. 长期资产文本优先；Git 只跟踪允许保留的内容，不以可审计之名牺牲可撤回性
2. 本地优先，云可选
3. 事实/知识/人格三维分层不混淆
4. 标准写进库，不绑工具
5. Agent 不得自动对外分享、发送第三方数据或把未授权推断写成事实
